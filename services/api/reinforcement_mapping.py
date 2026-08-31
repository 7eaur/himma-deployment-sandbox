"""Deterministic M03 reinforcement resolver.

This module is intentionally separate from the original 105-item catalog. It
uses the reviewed skill-family map to select only approved same-level
reinforcement candidates. Missing coverage is a safe hold; there is never a
random fallback.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from sqlalchemy.orm import Session

from db.models import AssessmentSession, Attempt, ContentItem, Skill


ROOT = Path(__file__).resolve().parents[2]
MAP_PATH = ROOT / "packages" / "content" / "src" / "reinforcement_skill_map_v1.json"


@lru_cache(maxsize=1)
def _mapping_rows() -> tuple[dict, ...]:
    payload = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    rules = payload.get("rules") or {}
    if rules.get("random_fallback") is not False:
        raise RuntimeError("Reinforcement mapping must explicitly forbid random fallback")
    if rules.get("same_level_only") is not True:
        raise RuntimeError("Reinforcement mapping must be same-level only")
    rows = payload.get("skills")
    if not isinstance(rows, list):
        raise RuntimeError("Invalid reinforcement skill map")
    return tuple(rows)


def mapping_for_skill(*, level_id: int, skill_code: str) -> dict | None:
    """Return the reviewed mapping row for one canonical skill."""
    return next(
        (
            row
            for row in _mapping_rows()
            if int(row["level"]) == int(level_id) and row["skill_code"] == skill_code
        ),
        None,
    )


def _canonical_id(item: ContentItem) -> str | None:
    return (item.template_data or {}).get("canonical_id")


def recommended_reinforcement_for_skill(
    db: Session,
    *,
    student_id: int,
    level_id: int,
    weakest_skill_id: int | None,
) -> int | None:
    """Select the first unused reviewed candidate available in the database.

    Candidate order is meaningful and comes from the reviewed mapping file. If
    the skill is uncovered, the candidate is not seeded yet, or all reviewed
    candidates were already used, return ``None`` so the existing supervisor
    hold flow can take over.
    """
    if weakest_skill_id is None:
        return None

    skill = db.query(Skill).filter(Skill.id == weakest_skill_id).first()
    if not skill or skill.level_id != level_id or not skill.canonical_skill_id:
        return None

    mapping = mapping_for_skill(level_id=level_id, skill_code=skill.canonical_skill_id)
    if not mapping or mapping.get("coverage") == "uncovered":
        return None

    candidates = list(mapping.get("candidates") or [])
    if not candidates:
        return None

    used_ids = {
        row[0]
        for row in db.query(Attempt.item_id)
        .join(AssessmentSession, AssessmentSession.id == Attempt.session_id)
        .join(ContentItem, ContentItem.id == Attempt.item_id)
        .filter(
            AssessmentSession.student_id == student_id,
            ContentItem.kind == "reinforcement_activity",
            ContentItem.level_id == level_id,
        )
        .all()
    }

    available = (
        db.query(ContentItem)
        .filter(
            ContentItem.kind == "reinforcement_activity",
            ContentItem.level_id == level_id,
            ContentItem.status == "approved",
        )
        .order_by(ContentItem.order_index, ContentItem.id)
        .all()
    )
    by_canonical = {
        canonical: item
        for item in available
        if (canonical := _canonical_id(item)) and item.id not in used_ids
    }

    for candidate in candidates:
        item = by_canonical.get(candidate)
        if item is not None:
            return item.id
    return None
