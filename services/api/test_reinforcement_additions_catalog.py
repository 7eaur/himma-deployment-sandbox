"""Contract tests for the M03 versioned reinforcement extension catalog."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "packages" / "content" / "src" / "reinforcement_additions_v1.json"


def _load() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def test_reinforcement_extension_preserves_original_catalog_and_adds_exactly_18_items():
    data = _load()
    assert data["catalog_version"] == "HIMMA-REINFORCEMENT-ADD-1.0"
    assert data["constraints"]["original_reinforcement_items_preserved"] == 15
    assert data["constraints"]["new_items"] == 18
    assert data["constraints"]["target_reinforcement_total"] == 33
    assert len(data["items"]) == 18

    by_level = {1: 0, 2: 0, 3: 0}
    for item in data["items"]:
        by_level[item["level"]] += 1
    assert by_level == {1: 7, 2: 6, 3: 5}


def test_reinforcement_ids_are_unique_and_match_the_approved_ranges():
    data = _load()
    ids = [item["canonical_id"] for item in data["items"]]
    assert len(ids) == len(set(ids))
    assert ids == [
        "L1-REIN-06", "L1-REIN-07", "L1-REIN-08", "L1-REIN-09",
        "L1-REIN-10", "L1-REIN-11", "L1-REIN-12",
        "L2-REIN-06", "L2-REIN-07", "L2-REIN-08", "L2-REIN-09",
        "L2-REIN-10", "L2-REIN-11",
        "L3-REIN-06", "L3-REIN-07", "L3-REIN-08", "L3-REIN-09",
        "L3-REIN-10",
    ]


def test_every_addition_has_target_family_threshold_and_verification_contract():
    data = _load()
    assert data["constraints"]["no_random_fallback"] is True
    assert data["constraints"]["verification_after_reinforcement"] is True
    for item in data["items"]:
        assert item["target_skill_family"]
        assert item["target_skills"]
        assert item["success_threshold"] == 80
        assert item["verification_required"] is True
        assert item["rounds"]


def test_audio_additions_do_not_silently_create_new_gaps_beyond_saa():
    data = _load()
    required = []
    for item in data["items"]:
        required.extend((item.get("media") or {}).get("new_audio_required", []))
    assert required == ["سَا"]


def test_shadda_gap_has_dedicated_reinforcement_content():
    data = _load()
    item = next(row for row in data["items"] if row["canonical_id"] == "L2-REIN-09")
    assert item["target_skill_family"] == "shadda"
    assert "قراءة كلمات الشدة" in item["target_skills"]
    assert [round_["answer"] for round_ in item["rounds"]] == [
        "قِطَّة", "سُلَّم", "تُفَّاح", "مُعَلِّم", "سَيَّارَة"
    ]
