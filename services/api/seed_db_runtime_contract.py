"""Persist the complete runtime content/media source contract into PostgreSQL.

Repository JSON/CSV files are import sources only. Student-facing runtime code must
never open them. This seed snapshots the approved source metadata and the resolved
media mapping into ContentItem.template_data so every later API read is DB-only.
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from db.database import SessionLocal
from db.models import ContentItem

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "packages" / "content" / "src"
CATALOG = CONTENT / "catalog.json"
ADDITIONS = (CONTENT / "reinforcement_additions_v1.json", CONTENT / "reinforcement_additions_v2.json")
VISUAL_PLAN = CONTENT / "visual_asset_plan_v1.json"
AUDIO_MANIFEST = ROOT / "assets" / "audio" / "HIMMA_AUDIO_V1" / "manifest.csv"
IMAGE_MAP = ROOT / "assets" / "education" / "developer" / "asset-map.json"
VERSION = "HIMMA-DB-RUNTIME-1.0"


def _json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        if default is not None:
            return default
        raise


def _key(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = re.sub(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]", "", value)
    value = value.replace("ـ", "")
    value = re.sub(r"[^\w\u0600-\u06ff]+", "", value, flags=re.UNICODE)
    return value.casefold()


def _audio_by_text() -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    try:
        with AUDIO_MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("status") != "approved":
                    continue
                asset_id = str(row.get("id") or "").strip()
                if not asset_id:
                    continue
                semantic = str(row.get("text_ar") or row.get("spoken_input") or "").strip()
                for value in (row.get("text_ar"), row.get("spoken_input")):
                    normalized = _key(str(value or ""))
                    if normalized:
                        result.setdefault(normalized, (asset_id, semantic))
    except OSError:
        pass
    return result


def _audio_semantics_by_id() -> dict[str, str]:
    return {asset_id: semantic for asset_id, semantic in _audio_by_text().values()}


def _image_by_text() -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    payload = _json(IMAGE_MAP, {"assets": []})
    for asset in payload.get("assets", []):
        asset_id = str(asset.get("id") or "").strip()
        semantic = str(asset.get("label_ar") or asset.get("alt_ar") or "").strip()
        if not asset_id:
            continue
        for value in (asset.get("label_ar"), asset.get("alt_ar")):
            normalized = _key(str(value or ""))
            if normalized:
                result.setdefault(normalized, (asset_id, semantic))
    return result


def _image_semantics_by_id() -> dict[str, str]:
    return {asset_id: semantic for asset_id, semantic in _image_by_text().values()}


def _project_addition(item: dict[str, Any], visual: dict[str, Any]) -> dict[str, Any]:
    projected = dict(item)
    canonical = str(item.get("canonical_id") or "")
    interaction = str(item.get("interaction") or "")
    reuse = (visual.get("reuse") or {}).get(canonical, {})
    audio_index = _audio_by_text()
    image_index = _image_by_text()
    required = {_key(str(value)) for value in (item.get("media") or {}).get("new_audio_required", [])}
    rounds: list[dict[str, Any]] = []

    for order_index, raw in enumerate(item.get("rounds", []), start=1):
        round_data = dict(raw)
        round_data["order_index"] = order_index
        media: list[dict[str, Any]] = []
        gaps: list[dict[str, Any]] = []
        audio_text = str(round_data.get("audio_text") or "").strip()
        if audio_text:
            found = audio_index.get(_key(audio_text))
            if found:
                media.append({"asset_id": found[0], "asset_type": "audio", "usage": "prompt", "semantic_text": audio_text})
            elif _key(audio_text) in required:
                gaps.append({"asset_type": "audio", "usage": "prompt", "semantic_text": audio_text, "status": "missing_approved_asset", "reason": "approved content requires a fixed audio asset that is not available"})

        sequence = round_data.get("sequence")
        if isinstance(sequence, list):
            for value in sequence:
                semantic = str(value)
                asset_id = str(reuse.get(semantic) or "").strip()
                if not asset_id and interaction == "memory_sequence":
                    found = image_index.get(_key(semantic))
                    asset_id = found[0] if found else ""
                if asset_id:
                    media.append({"asset_id": asset_id, "asset_type": "image", "usage": "illustration", "semantic_text": semantic})
        if media:
            round_data["media"] = media
        if gaps:
            round_data["media_gaps"] = gaps
        rounds.append(round_data)
    projected["rounds"] = rounds
    return projected


def _sources() -> dict[str, dict[str, Any]]:
    base = _json(CATALOG)
    result = {str(item["canonical_id"]): item for item in base.get("items", [])}
    visual = _json(VISUAL_PLAN, {})
    for path in ADDITIONS:
        payload = _json(path, {"items": []})
        for item in payload.get("items", []):
            projected = _project_addition(item, visual)
            result[str(projected["canonical_id"])] = projected
    return result


def _option_order(step, semantic: str | None, position: int) -> int | None:
    options = sorted(step.options, key=lambda option: option.order_index)
    normalized = _key(semantic or "")
    if normalized:
        for option in options:
            if _key(option.text) == normalized:
                return int(option.order_index)
    return int(options[position].order_index) if position < len(options) else None


def _resolved_step_assets(item, step, source_round: dict[str, Any]) -> list[dict[str, Any]]:
    source_media = list(source_round.get("media") or [])
    source_by_id: dict[str, list[dict[str, Any]]] = {}
    for media in source_media:
        source_by_id.setdefault(str(media.get("asset_id") or ""), []).append(media)
    audio_semantics = _audio_semantics_by_id()
    image_semantics = _image_semantics_by_id()
    result: list[dict[str, Any]] = []
    image_position = 0

    links = sorted(step.assets, key=lambda link: link.id or 0)
    if links:
        for link in links:
            candidates = source_by_id.get(link.manifest_asset_id, [])
            source = candidates.pop(0) if candidates else {}
            semantic = str(source.get("semantic_text") or "").strip()
            if not semantic:
                semantic = audio_semantics.get(link.manifest_asset_id, "") if link.asset_type == "audio" else image_semantics.get(link.manifest_asset_id, "")
            option_order = None
            if link.asset_type == "image" and link.usage_context in {"choice", "illustration"}:
                option_order = _option_order(step, semantic, image_position)
                options = sorted(step.options, key=lambda option: option.order_index)
                if option_order is not None:
                    matched = next((option for option in options if option.order_index == option_order), None)
                    if matched is not None:
                        semantic = matched.text
                image_position += 1
            result.append({"asset_id": link.manifest_asset_id, "asset_type": link.asset_type, "usage": link.usage_context, "semantic_text": semantic or None, "option_order_index": option_order})
        return result

    # Additive maintenance content historically kept reusable media in its JSON
    # projection rather than DB link rows. Snapshot it into DB now.
    for media in source_media:
        asset_id = str(media.get("asset_id") or "").strip()
        asset_type = str(media.get("asset_type") or media.get("type") or "").strip()
        if not asset_id or not asset_type:
            continue
        semantic = str(media.get("semantic_text") or "").strip()
        option_order = None
        if asset_type == "image" and str(media.get("usage") or "") in {"choice", "illustration"}:
            option_order = _option_order(step, semantic, image_position)
            image_position += 1
        result.append({"asset_id": asset_id, "asset_type": asset_type, "usage": media.get("usage"), "semantic_text": semantic or None, "option_order_index": option_order})
    return result


def _resolved_item_assets(item, source: dict[str, Any]) -> list[dict[str, Any]]:
    source_assets = {str(value.get("asset_id") or ""): value for value in source.get("item_assets", [])}
    image_semantics = _image_semantics_by_id()
    result = []
    for link in sorted(item.assets, key=lambda value: value.id or 0):
        source_asset = source_assets.get(link.manifest_asset_id, {})
        semantic = str(source_asset.get("semantic_text") or image_semantics.get(link.manifest_asset_id) or "").strip()
        result.append({"asset_id": link.manifest_asset_id, "asset_type": link.asset_type, "usage": link.usage_context, "semantic_text": semantic or None})
    return result


def run_seed() -> int:
    sources = _sources()
    db = SessionLocal()
    changed = 0
    try:
        items = db.query(ContentItem).all()
        for item in items:
            data = dict(item.template_data or {})
            canonical = str(data.get("canonical_id") or item.stable_key)
            source = sources.get(canonical)
            if source is None:
                raise RuntimeError(f"No import source found for runtime item {canonical}")
            source_rounds = {int(value.get("order_index") or index): value for index, value in enumerate(source.get("rounds", []), start=1)}
            rounds = []
            for step in sorted(item.steps, key=lambda value: value.order_index):
                source_round = source_rounds.get(int(step.order_index), {})
                rounds.append({
                    "order_index": int(step.order_index),
                    "source": source_round,
                    "assets": _resolved_step_assets(item, step, source_round),
                    "media_gaps": list(source_round.get("media_gaps") or []),
                })
            runtime = {
                "version": VERSION,
                "canonical_id": canonical,
                "source_item": source,
                "rounds": rounds,
                "item_assets": _resolved_item_assets(item, source),
            }
            if data.get("db_runtime") != runtime:
                data["db_runtime"] = runtime
                item.template_data = data
                changed += 1
        db.commit()
        return changed
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print(f"DB runtime contract persisted: changed={run_seed()}")
