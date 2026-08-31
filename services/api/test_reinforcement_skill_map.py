"""M03 contract tests for deterministic skill-family reinforcement mapping."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAP_PATH = ROOT / "packages" / "content" / "src" / "reinforcement_skill_map_v1.json"


def _load() -> dict:
    return json.loads(MAP_PATH.read_text(encoding="utf-8"))


def test_mapping_covers_all_44_canonical_skills_once():
    data = _load()
    skills = data["skills"]
    assert len(skills) == 44
    keys = [(row["level"], row["skill_code"]) for row in skills]
    assert len(keys) == len(set(keys))


def test_mapping_never_allows_random_or_cross_level_fallback():
    rules = _load()["rules"]
    assert rules["same_level_only"] is True
    assert rules["approved_candidates_only"] is True
    assert rules["random_fallback"] is False
    assert rules["uncovered_skill_action"] == "supervisor_hold"
    assert rules["verification_after_reinforcement"] is True


def test_approved_2026_08_29_gap_closure_leaves_no_uncovered_skills():
    uncovered = [
        (row["level"], row["skill_code"], row["skill_name"])
        for row in _load()["skills"]
        if row["coverage"] == "uncovered"
    ]
    assert uncovered == []


def test_shadda_has_a_direct_dedicated_candidate():
    row = next(r for r in _load()["skills"] if r["skill_code"] == "shadda_word_reading")
    assert row["coverage"] == "direct"
    assert row["candidates"] == ["L2-REIN-09"]


def test_every_candidate_stays_inside_the_skill_level():
    for row in _load()["skills"]:
        prefix = f"L{row['level']}-REIN-"
        assert all(candidate.startswith(prefix) for candidate in row["candidates"])
