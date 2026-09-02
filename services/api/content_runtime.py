"""DB-only student-facing content helpers.

All academic/display metadata is imported into PostgreSQL by seed_all. Runtime
requests must never open repository JSON/CSV content files and must never parse
legacy ContentStep.prompt_text to construct the student experience.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

from db.models import ContentItem, ContentStep


DB_RUNTIME_VERSION = "HIMMA-DB-RUNTIME-1.0"
READ = {"read_aloud", "timed_read_aloud"}
LISTEN = {"listen_choose_one", "listen_choose_image", "listen_choose_many"}
ORDER = {"sequence", "memory_sequence", "path_sequence", "build_word"}


def semantic_key(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = re.sub(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]", "", value)
    value = value.replace("ـ", "")
    value = re.sub(r"[^\w\u0600-\u06ff]+", "", value, flags=re.UNICODE)
    if value.startswith("ال"):
        value = value[2:]
    return value.casefold()


def canonical_id(item: ContentItem) -> str:
    data = item.template_data or {}
    return str(data.get("canonical_id") or item.stable_key)


def canonical_interaction(item: ContentItem) -> str:
    data = item.template_data or {}
    return str(data.get("canonical_interaction_type") or item.interaction_type)


def _db_runtime(item: ContentItem) -> dict[str, Any]:
    data = item.template_data or {}
    runtime = data.get("db_runtime") or {}
    if runtime and runtime.get("version") != DB_RUNTIME_VERSION:
        return {}
    return runtime


def catalog_item(item: ContentItem) -> dict[str, Any]:
    """Historical/import source snapshot persisted in DB; never read from disk."""
    return dict(_db_runtime(item).get("source_item") or {})


def _runtime_round(item: ContentItem, step: ContentStep) -> dict[str, Any]:
    for value in _db_runtime(item).get("rounds", []):
        if int(value.get("order_index") or 0) == int(step.order_index):
            return value
    return {}


def round_data(item: ContentItem, step: ContentStep) -> dict[str, Any]:
    """Compatibility view backed only by the persisted DB runtime snapshot."""
    runtime = _runtime_round(item, step)
    source = dict(runtime.get("source") or {})
    source["media"] = [
        {
            "asset_id": value.get("asset_id"),
            "asset_type": value.get("asset_type"),
            "type": value.get("asset_type"),
            "usage": value.get("usage"),
            "semantic_text": value.get("semantic_text"),
        }
        for value in runtime.get("assets", [])
    ]
    source["media_gaps"] = list(runtime.get("media_gaps") or [])
    return source


def _presentation(item: ContentItem, step: ContentStep) -> dict[str, Any]:
    data = item.template_data or {}
    if item.kind == "pretest_question":
        return dict(data.get("pretest_experience") or {})
    if item.kind == "posttest_question":
        return dict(data.get("posttest_experience") or {})
    if item.kind in {"core_activity", "reinforcement_activity"}:
        experience = data.get("learning_experience") or {}
        for value in experience.get("rounds", []):
            if int(value.get("round_number") or 0) == int(step.order_index):
                return dict(value)
    return {}


def presentation_data(item: ContentItem, step: ContentStep) -> dict[str, Any]:
    """Explicit student-facing display contract stored in PostgreSQL."""
    return _presentation(item, step)


def _fallback_instruction(interaction: str) -> str:
    if interaction in LISTEN:
        return "استمع جيدًا، ثم اختر الإجابة المناسبة."
    if interaction in READ:
        return "اقرأ النص الظاهر بصوت واضح، ثم أرسل تسجيلك."
    if interaction == "memory_sequence":
        return "تذكّر العناصر جيدًا، ثم أعد ترتيبها كما ظهرت."
    if interaction in ORDER:
        return "اضغط على العناصر بالترتيب الصحيح."
    if interaction in {"choose_image", "choose_many"}:
        return "انظر جيدًا، ثم اختر العناصر المطلوبة."
    return "اقرأ المطلوب، ثم اختر الإجابة المناسبة."


def instruction_text(item: ContentItem, step: ContentStep) -> str:
    """Return only an explicit DB presentation instruction; never parse prompt_text."""
    value = str(_presentation(item, step).get("instruction_text") or "").strip()
    return value or _fallback_instruction(canonical_interaction(item))


def media_gaps(item: ContentItem, step: ContentStep) -> list[dict[str, Any]]:
    return list(_runtime_round(item, step).get("media_gaps") or [])


def _option_id_by_order(step: ContentStep, order_index: Any) -> int | None:
    try:
        wanted = int(order_index)
    except (TypeError, ValueError):
        return None
    option = next((value for value in step.options if int(value.order_index) == wanted), None)
    return int(option.id) if option is not None else None


def step_assets(item: ContentItem, step: ContentStep) -> list[dict[str, Any]]:
    runtime_assets = list(_runtime_round(item, step).get("assets") or [])
    if runtime_assets:
        return [
            {
                "asset_id": str(value.get("asset_id") or ""),
                "asset_type": str(value.get("asset_type") or ""),
                "usage": value.get("usage"),
                "semantic_text": value.get("semantic_text"),
                "url": f"/api/media/{value.get('asset_id')}",
                "option_id": _option_id_by_order(step, value.get("option_order_index")),
            }
            for value in runtime_assets
            if value.get("asset_id") and value.get("asset_type")
        ]

    # Defensive compatibility for a partially seeded development DB. This reads
    # only relational DB links and never repository content files.
    result: list[dict[str, Any]] = []
    image_index = 0
    options = sorted(step.options, key=lambda value: value.order_index)
    for link in sorted(step.assets, key=lambda value: value.id or 0):
        option_id = None
        semantic = None
        if link.asset_type == "image" and link.usage_context in {"choice", "illustration"} and image_index < len(options):
            option_id = int(options[image_index].id)
            semantic = options[image_index].text
            image_index += 1
        result.append({
            "asset_id": link.manifest_asset_id,
            "asset_type": link.asset_type,
            "usage": link.usage_context,
            "semantic_text": semantic,
            "url": f"/api/media/{link.manifest_asset_id}",
            "option_id": option_id,
        })
    return result


def item_assets(item: ContentItem) -> list[dict[str, Any]]:
    runtime_assets = list(_db_runtime(item).get("item_assets") or [])
    if runtime_assets:
        return [
            {
                "asset_id": str(value.get("asset_id") or ""),
                "asset_type": str(value.get("asset_type") or ""),
                "usage": value.get("usage"),
                "semantic_text": value.get("semantic_text"),
                "url": f"/api/media/{value.get('asset_id')}",
                "option_id": None,
            }
            for value in runtime_assets
            if value.get("asset_id") and value.get("asset_type")
        ]
    return [
        {
            "asset_id": link.manifest_asset_id,
            "asset_type": link.asset_type,
            "usage": link.usage_context,
            "semantic_text": None,
            "url": f"/api/media/{link.manifest_asset_id}",
            "option_id": None,
        }
        for link in sorted(item.assets, key=lambda value: value.id or 0)
    ]
