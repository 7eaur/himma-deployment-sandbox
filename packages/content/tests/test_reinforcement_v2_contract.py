import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V2 = ROOT / "content" / "src" / "reinforcement_additions_v2.json"
MAP = ROOT / "content" / "src" / "reinforcement_skill_map_v1.json"


def test_v2_contains_two_explicitly_approved_gap_items():
    payload = json.loads(V2.read_text(encoding="utf-8"))
    items = {item["canonical_id"]: item for item in payload["items"]}
    assert set(items) == {"L3-REIN-11", "L3-REIN-12"}
    assert len(items["L3-REIN-11"]["rounds"]) == 5
    assert items["L3-REIN-11"]["target_skill_family"] == "literal_comprehension"
    assert len(items["L3-REIN-12"]["rounds"]) == 5
    assert items["L3-REIN-12"]["target_skill_family"] == "sentence_structure"
    assert payload["constraints"]["no_random_fallback"] is True
    assert payload["constraints"]["verification_after_reinforcement"] is True


def test_mapping_closes_only_the_approved_gaps():
    payload = json.loads(MAP.read_text(encoding="utf-8"))
    rows = {(int(row["level"]), row["skill_code"]): row for row in payload["skills"]}

    sukoon = rows[(2, "sukoon_word_reading")]
    assert sukoon["candidates"] == ["L2-REIN-02"]
    assert sukoon["coverage"] == "supporting"

    literal = rows[(3, "literal_comprehension")]
    assert literal["candidates"] == ["L3-REIN-11"]
    assert literal["coverage"] == "direct"

    sentence = rows[(3, "sentence_building")]
    assert sentence["candidates"] == ["L3-REIN-12"]
    assert sentence["coverage"] == "direct"
