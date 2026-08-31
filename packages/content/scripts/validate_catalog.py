#!/usr/bin/env python3
"""Strict, dependency-free validation for the Himma approved catalog."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import unicodedata
import uuid
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import compile_catalog


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def load_audio_rows() -> dict[str, dict[str, str]]:
    with compile_catalog.AUDIO_MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row["id"]: row for row in csv.DictReader(handle)}


def _document_text() -> str:
    paragraph_tag = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"
    text_tag = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"
    with zipfile.ZipFile(compile_catalog.ORIGINAL_SOURCE) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    paragraphs = [
        "".join(node.text or "" for node in paragraph.iter(text_tag))
        for paragraph in root.iter(paragraph_tag)
    ]
    return _document_key("\n".join(paragraph for paragraph in paragraphs if paragraph))


def _document_key(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).replace("\\", "")
    return re.sub(r"\s+", " ", value).strip()


def validate_original_sequence(items: list[dict[str, Any]], errors: list[str]) -> None:
    """Prove that every catalog field and round occurs in the original DOCX in order."""
    document = _document_text()
    cursor = 0
    for item in items:
        expected_fragments = [
            item["title"],
            item["source_skill_name"],
            item["source_method"],
            *(round_data["source_text"] for round_data in item["rounds"]),
        ]
        if item.get("criterion"):
            expected_fragments.append(item["criterion"])
        if item.get("note"):
            expected_fragments.append(item["note"])
        for fragment in expected_fragments:
            normalized = _document_key(fragment)
            position = document.find(normalized, cursor)
            if position < 0:
                errors.append(
                    f"{item['canonical_id']}: catalog text is absent or out of order in the original DOCX: {fragment}"
                )
                break
            cursor = position + len(normalized)


def validate() -> list[str]:
    errors: list[str] = []
    catalog_path = compile_catalog.OUTPUT
    require(catalog_path.exists(), f"Missing generated catalog: {catalog_path}", errors)
    if errors:
        return errors

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    generated = compile_catalog.build_catalog()
    require(catalog == generated, "catalog.json has drifted from the deterministic compiler output", errors)
    require(catalog.get("schema_version") == 1, "schema_version must be 1", errors)
    require(catalog.get("catalog_version") == compile_catalog.CATALOG_VERSION, "unexpected catalog_version", errors)

    source = catalog.get("source", {})
    require(source.get("original_sha256") == compile_catalog.file_sha256(compile_catalog.ORIGINAL_SOURCE), "original DOCX hash mismatch", errors)
    require(source.get("derived_sha256") == compile_catalog.file_sha256(compile_catalog.DERIVED_SOURCE), "derived Markdown hash mismatch", errors)

    items = catalog.get("items", [])
    skills = catalog.get("skills", [])
    require(len(items) == 105, f"expected 105 items, got {len(items)}", errors)
    require(len(catalog.get("levels", [])) == 3, "expected exactly three levels", errors)
    validate_original_sequence(items, errors)

    kind_counts = Counter(item.get("kind") for item in items)
    require(kind_counts == Counter({
        "pretest_question": 30,
        "posttest_question": 30,
        "core_activity": 30,
        "reinforcement_activity": 15,
    }), f"wrong kind counts: {dict(kind_counts)}", errors)

    for kind in ("pretest_question", "posttest_question"):
        distribution = Counter(item.get("level_id") for item in items if item.get("kind") == kind)
        require(distribution == Counter({1: 10, 2: 12, 3: 8}), f"wrong {kind} level distribution: {dict(distribution)}", errors)
    for level_id in (1, 2, 3):
        core = [item for item in items if item.get("level_id") == level_id and item.get("kind") == "core_activity"]
        reinforcement = [item for item in items if item.get("level_id") == level_id and item.get("kind") == "reinforcement_activity"]
        require(len(core) == 10, f"level {level_id} must have 10 core activities", errors)
        require(len(reinforcement) == 5, f"level {level_id} must have 5 reinforcement activities", errors)

    skill_by_id = {skill["skill_id"]: skill for skill in skills}
    require(len(skill_by_id) == len(skills), "duplicate skill_id", errors)
    item_ids: set[str] = set()
    stable_keys: set[str] = set()
    round_ids: set[str] = set()
    allowed = set(catalog.get("constraints", {}).get("allowed_interactions", []))
    require(allowed == compile_catalog.INTERACTIONS, "allowed interaction enum drift", errors)

    audio_rows = load_audio_rows()
    image_data = json.loads(compile_catalog.IMAGE_MAP.read_text(encoding="utf-8"))
    image_by_id = {asset["id"]: asset for asset in image_data["assets"]}
    image_manifest = json.loads((compile_catalog.REPO_ROOT / "assets/education/ASSET_MANIFEST.json").read_text(encoding="utf-8"))
    image_manifest_paths = {entry["path"] for entry in image_manifest["files"]}

    all_gaps: list[dict[str, str]] = []
    for item in items:
        item_id = item.get("canonical_id")
        require(isinstance(item_id, str) and bool(item_id), "item without canonical_id", errors)
        require(item_id not in item_ids, f"duplicate canonical_id: {item_id}", errors)
        item_ids.add(item_id)

        stable_key = item.get("stable_key")
        try:
            uuid.UUID(stable_key)
        except (TypeError, ValueError, AttributeError):
            errors.append(f"{item_id}: invalid stable_key")
        require(stable_key not in stable_keys, f"duplicate stable_key: {stable_key}", errors)
        stable_keys.add(stable_key)

        require(item.get("interaction_type") in allowed, f"{item_id}: unknown interaction type", errors)
        require(item.get("skill_id") in skill_by_id, f"{item_id}: unknown skill_id", errors)
        if item.get("skill_id") in skill_by_id:
            skill = skill_by_id[item["skill_id"]]
            require(skill["level_id"] == item.get("level_id"), f"{item_id}: skill level mismatch", errors)
            require(skill["name"] == item.get("skill_name"), f"{item_id}: canonical skill name mismatch", errors)
        require(bool(item.get("source_skill_name")), f"{item_id}: missing original skill wording", errors)
        require(bool(item.get("source_method")), f"{item_id}: missing interaction method", errors)
        require(bool(item.get("rounds")), f"{item_id}: no approved rounds", errors)

        checksum_payload = dict(item)
        checksum = checksum_payload.pop("checksum", None)
        expected_checksum = hashlib.sha256(compile_catalog.canonical_json(checksum_payload).encode("utf-8")).hexdigest()
        require(checksum == expected_checksum, f"{item_id}: checksum mismatch", errors)

        media_blocks = [item.get("item_assets", [])]
        for round_data in item.get("rounds", []):
            round_id = round_data.get("round_id")
            require(round_id not in round_ids, f"duplicate round_id: {round_id}", errors)
            round_ids.add(round_id)
            require(bool(round_data.get("source_text")), f"{round_id}: empty approved round", errors)
            media_blocks.append(round_data.get("media", []))
            for gap in round_data.get("media_gaps", []):
                require(gap.get("status") == "declared_missing", f"{round_id}: undeclared media state", errors)
                require(bool(gap.get("reason")) and bool(gap.get("impact")), f"{round_id}: incomplete media gap declaration", errors)
                all_gaps.append({"item_id": item_id, "round_id": round_id, **gap})

        for media in (entry for block in media_blocks for entry in block):
            asset_id = media.get("asset_id")
            asset_type = media.get("asset_type")
            semantic_text = media.get("semantic_text", "")
            require(bool(asset_id) and "." not in asset_id, f"{item_id}: use stable manifest IDs, not filenames ({asset_id})", errors)
            if asset_type == "audio":
                row = audio_rows.get(asset_id)
                require(row is not None, f"{item_id}: unknown audio asset {asset_id}", errors)
                if row:
                    semantic_matches = {
                        compile_catalog.semantic_key(row["text_ar"]),
                        compile_catalog.semantic_key(row["spoken_input"]),
                    }
                    require(compile_catalog.semantic_key(semantic_text) in semantic_matches, f"{item_id}: audio {asset_id} does not say {semantic_text}", errors)
                    require((compile_catalog.AUDIO_MANIFEST.parent / "wav_master" / row["filename_wav"]).is_file(), f"missing WAV for {asset_id}", errors)
                    require((compile_catalog.AUDIO_MANIFEST.parent / "web_mp3" / row["filename_mp3"]).is_file(), f"missing MP3 for {asset_id}", errors)
            elif asset_type == "image":
                asset = image_by_id.get(asset_id)
                require(asset is not None, f"{item_id}: unknown image asset {asset_id}", errors)
                if asset:
                    semantic_key = compile_catalog.image_semantic_key(semantic_text)
                    exact = semantic_key == compile_catalog.image_semantic_key(asset["label_ar"])
                    aliased = compile_catalog.IMAGE_LABEL_ALIASES.get(semantic_key) == asset_id
                    require(exact or aliased, f"{item_id}: image {asset_id} does not depict {semantic_text}", errors)
                    webp_path = asset["files"]["webp"]
                    require(webp_path in image_manifest_paths, f"{item_id}: image {asset_id} absent from package manifest", errors)
                    require((compile_catalog.REPO_ROOT / "assets/education" / webp_path).is_file(), f"{item_id}: missing image binary for {asset_id}", errors)
            else:
                errors.append(f"{item_id}: unsupported asset_type {asset_type}")

    require(all_gaps == catalog.get("media_gaps"), "top-level media gap inventory is not exact", errors)
    require(len(all_gaps) == catalog.get("summary", {}).get("declared_media_gap_count"), "media gap summary mismatch", errors)
    require({gap["asset_type"] for gap in all_gaps} <= {"audio", "image"}, "unknown gap asset type", errors)
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("CONTENT CATALOG: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    catalog = json.loads(compile_catalog.OUTPUT.read_text(encoding="utf-8"))
    print(
        "CONTENT CATALOG: PASS — "
        f"{len(catalog['items'])} items, {len(catalog['skills'])} canonical skills, "
        f"{len(catalog['media_gaps'])} explicit V1 media gaps"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
