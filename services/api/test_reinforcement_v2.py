import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V2_PATH = ROOT / "packages" / "content" / "src" / "reinforcement_additions_v2.json"
MAP_PATH = ROOT / "packages" / "content" / "src" / "reinforcement_skill_map_v1.json"


def _rows():
    payload = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    return {(int(row["level"]), row["skill_code"]): row for row in payload["skills"]}


def test_v2_gap_release_is_exactly_two_approved_l3_items():
    payload = json.loads(V2_PATH.read_text(encoding="utf-8"))
    assert payload["catalog_version"] == "HIMMA-REINFORCEMENT-ADD-2.0"
    assert payload["constraints"]["new_items"] == 2
    assert payload["constraints"]["no_random_fallback"] is True
    assert payload["constraints"]["verification_after_reinforcement"] is True

    items = {item["canonical_id"]: item for item in payload["items"]}
    assert set(items) == {"L3-REIN-11", "L3-REIN-12"}
    assert items["L3-REIN-11"]["target_skill_family"] == "literal_comprehension"
    assert items["L3-REIN-11"]["interaction"] == "choose_one"
    assert len(items["L3-REIN-11"]["rounds"]) == 5
    assert items["L3-REIN-12"]["target_skill_family"] == "sentence_structure"
    assert items["L3-REIN-12"]["interaction"] == "sequence"
    assert len(items["L3-REIN-12"]["rounds"]) == 5


def test_three_previously_uncovered_skills_have_approved_candidates():
    rows = _rows()
    assert rows[(2, "sukoon_word_reading")]["candidates"] == ["L2-REIN-02"]
    assert rows[(2, "sukoon_word_reading")]["coverage"] == "supporting"
    assert rows[(3, "literal_comprehension")]["candidates"] == ["L3-REIN-11"]
    assert rows[(3, "literal_comprehension")]["coverage"] == "direct"
    assert rows[(3, "sentence_building")]["candidates"] == ["L3-REIN-12"]
    assert rows[(3, "sentence_building")]["coverage"] == "direct"


def test_gap_rows_never_use_random_or_cross_level_fallback():
    payload = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    assert payload["rules"]["same_level_only"] is True
    assert payload["rules"]["approved_candidates_only"] is True
    assert payload["rules"]["random_fallback"] is False
