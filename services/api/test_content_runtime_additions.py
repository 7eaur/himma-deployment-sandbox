"""Regression coverage for additive reinforcement media projection."""

import seed_all
from content_runtime import canonical_interaction, media_gaps, step_assets
from db.database import SessionLocal
from db.models import ContentItem


def _seed_full_catalog():
    result = seed_all.run_seed_all()
    assert result["total_items"] == 125
    assert result["db_runtime_items"] == 125


def _item(db, canonical_id: str):
    return next(
        row
        for row in db.query(ContentItem).filter(ContentItem.kind == "reinforcement_activity").all()
        if (row.template_data or {}).get("canonical_id") == canonical_id
    )


def test_memory_reinforcement_reuses_approved_vocabulary_images():
    _seed_full_catalog()
    db = SessionLocal()
    try:
        item = _item(db, "L1-REIN-10")
        assert canonical_interaction(item) == "memory_sequence"
        assets = step_assets(item, item.steps[0])
        assert [(asset["asset_id"], asset["semantic_text"]) for asset in assets] == [
            ("VOC-04", "قلم"),
            ("VOC-10", "كرة"),
        ]
        assert all(asset["asset_type"] == "image" for asset in assets)
        assert all(asset["url"].startswith("/api/media/") for asset in assets)
        assert all(asset["option_id"] is not None for asset in assets)
    finally:
        db.close()


def test_listen_reinforcement_reuses_approved_audio_manifest_asset():
    _seed_full_catalog()
    db = SessionLocal()
    try:
        item = _item(db, "L1-REIN-06")
        assets = step_assets(item, item.steps[0])
        assert len(assets) == 1
        assert assets[0]["asset_id"] == "LET-01"
        assert assets[0]["asset_type"] == "audio"
        assert assets[0]["semantic_text"] == "م"
        assert media_gaps(item, item.steps[0]) == []
    finally:
        db.close()


def test_missing_saa_audio_is_explicit_neutral_gap_not_fake_asset():
    _seed_full_catalog()
    db = SessionLocal()
    try:
        item = _item(db, "L2-REIN-08")
        step = item.steps[3]
        assert step_assets(item, step) == []
        gaps = media_gaps(item, step)
        assert len(gaps) == 1
        assert gaps[0]["asset_type"] == "audio"
        assert gaps[0]["semantic_text"] == "سَا"
        assert gaps[0]["status"] == "missing_approved_asset"
    finally:
        db.close()


def test_sequence_reuses_only_semantically_approved_images():
    _seed_full_catalog()
    db = SessionLocal()
    try:
        item = _item(db, "L1-REIN-12")
        first_round_assets = step_assets(item, item.steps[0])
        assert [(asset["asset_id"], asset["semantic_text"]) for asset in first_round_assets] == [
            ("HIMMA-GEN-SEQ-001", "غسل اليدين"),
            ("HIMMA-GEN-SEQ-002", "الأكل"),
        ]
        second_round_assets = step_assets(item, item.steps[1])
        assert [(asset["asset_id"], asset["semantic_text"]) for asset in second_round_assets] == [
            ("SEQ-01", "زرع البذرة"),
            ("SEQ-03", "ظهور النبتة"),
        ]
        assert all(asset["url"].startswith("/api/media/") for asset in first_round_assets + second_round_assets)
    finally:
        db.close()
