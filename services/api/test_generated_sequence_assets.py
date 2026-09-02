"""Regression coverage for approved generated sequence visual assets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import media as media_module
import seed_all
from content_runtime import canonical_id
from db.database import SessionLocal
from db.models import ContentItem

REPO_ROOT = Path(__file__).resolve().parents[2]
EDUCATION_ROOT = REPO_ROOT / "assets" / "education"
GENERATED_MAP = EDUCATION_ROOT / "developer" / "generated-sequence-map.json"
VISUAL_PLAN = REPO_ROOT / "packages" / "content" / "src" / "visual_asset_plan_v1.json"

EXPECTED = {
    "HIMMA-GEN-SEQ-001": ("L1-REIN-12", "غسل اليدين"),
    "HIMMA-GEN-SEQ-002": ("L1-REIN-12", "الأكل"),
    "HIMMA-GEN-SEQ-003": ("L1-REIN-12", "فتح الكتاب"),
    "HIMMA-GEN-SEQ-004": ("L1-REIN-12", "سقي الزهرة"),
    "HIMMA-GEN-SEQ-005": ("L1-REIN-12", "لبس الحذاء"),
    "HIMMA-GEN-SEQ-006": ("L1-REIN-12", "الخروج من المنزل"),
    "HIMMA-GEN-SEQ-007": ("L3-REIN-10", "دخول المكتبة"),
    "HIMMA-GEN-SEQ-008": ("L3-REIN-10", "الذهاب إلى الشاطئ"),
    "HIMMA-GEN-SEQ-009": ("L3-REIN-10", "اللعب بالرمل"),
    "HIMMA-GEN-SEQ-010": ("L3-REIN-10", "تنظيف المكان"),
}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_generated_sequence_overlay_is_complete_and_binary_safe():
    data = _json(GENERATED_MAP)
    assert data["asset_count"] == 10
    assets = data["assets"]
    assert {asset["id"] for asset in assets} == set(EXPECTED)
    assert len({asset["id"] for asset in assets}) == 10

    for asset in assets:
        assert asset["contains_text"] is False
        assert asset["aspect_ratio"] == "4:3"
        relative = asset["files"]["webp_small"]
        path = (EDUCATION_ROOT / relative).resolve()
        assert EDUCATION_ROOT.resolve() in path.parents
        assert path.is_file(), relative
        payload = path.read_bytes()
        assert payload[:4] == b"RIFF"
        assert payload[8:12] == b"WEBP"
        assert hashlib.sha256(payload).hexdigest() == asset["sha256"]["webp_small"]
        assert asset["dimensions"]["webp_small"] == {"width": 240, "height": 180}


def test_visual_plan_has_no_remaining_generated_sequence_gap():
    plan = _json(VISUAL_PLAN)
    assert plan["generate"] == []
    generated = {row["id"]: row for row in plan["generated_assets"]}
    assert set(generated) == set(EXPECTED)
    for asset_id, (activity, label) in EXPECTED.items():
        assert generated[asset_id]["activity"] == activity
        assert generated[asset_id]["label_ar"] == label
        assert plan["reuse"][activity][label] == asset_id


def test_runtime_projects_all_generated_sequence_asset_ids_from_database():
    result = seed_all.run_seed_all()
    assert result["db_runtime_items"] == 125
    db = SessionLocal()
    try:
        by_canonical = {canonical_id(item): item for item in db.query(ContentItem).all()}
        for wanted in ("L1-REIN-12", "L3-REIN-10"):
            runtime = (by_canonical[wanted].template_data or {})["db_runtime"]
            projected_ids = {
                str(media_entry.get("asset_id"))
                for round_data in runtime.get("rounds", [])
                for media_entry in round_data.get("assets", [])
                if media_entry.get("asset_type") == "image"
            }
            expected_ids = {
                asset_id
                for asset_id, (activity, _label) in EXPECTED.items()
                if activity == wanted
            }
            assert expected_ids <= projected_ids
    finally:
        db.close()


def test_generated_assets_are_served_from_approved_media_index():
    for asset_id in EXPECTED:
        path, media_type = media_module._ASSETS[asset_id]
        assert path.is_file()
        assert media_type == "image/webp"
