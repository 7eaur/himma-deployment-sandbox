"""Seed the complete currently approved Himma runtime content set.

Use this entrypoint for fresh/repeatable environments after M03. It preserves
`seed.py` as the immutable 105-item baseline seeder while adding the accepted
maintenance extensions, Student Experience v2, and the latest user-approved
30-question pretest presentation/content overlay.
"""

from __future__ import annotations

import json
from pathlib import Path

import seed
import seed_reinforcement_additions
import seed_reinforcement_additions_v2
import seed_student_choice_corrections
import seed_student_experience_v2
import seed_pretest_experience_2026_09_01
from db.database import SessionLocal
from db.models import ContentItem


ROOT = Path(__file__).resolve().parents[2]
BASE_CATALOG = ROOT / "packages" / "content" / "src" / "catalog.json"
PRETEST_VERSION = "HIMMA-PRETEST-2026-09-01"


def _base_stable_keys() -> set[str]:
    payload = json.loads(BASE_CATALOG.read_text(encoding="utf-8"))
    return {str(item["stable_key"]) for item in payload["items"]}


def _base_is_complete() -> bool:
    required = _base_stable_keys()
    db = SessionLocal()
    try:
        present = {
            row[0]
            for row in db.query(ContentItem.stable_key).filter(ContentItem.stable_key.in_(required)).all()
        }
        return required == present
    finally:
        db.close()


def run_seed_all() -> dict[str, int]:
    if not _base_is_complete():
        seed.run_seed()

    v1_created = seed_reinforcement_additions.run_seed()
    v2_created = seed_reinforcement_additions_v2.run_seed()
    choice_corrections_created = seed_student_choice_corrections.run_seed()
    student_experience_changes = seed_student_experience_v2.run_seed()
    pretest_experience_changes = seed_pretest_experience_2026_09_01.run_seed()

    db = SessionLocal()
    try:
        all_items = db.query(ContentItem).all()
        total = len(all_items)
        base_count = db.query(ContentItem).filter(ContentItem.stable_key.in_(_base_stable_keys())).count()
        reinforcement_count = db.query(ContentItem).filter(ContentItem.kind == "reinforcement_activity").count()
        v2_marked = sum(1 for item in all_items if (item.template_data or {}).get("student_experience_version") == "HIMMA-STUDENT-EXPERIENCE-2.0")
        pretest_marked = sum(
            1 for item in all_items
            if item.kind == "pretest_question" and (item.template_data or {}).get("pretest_experience_version") == PRETEST_VERSION
        )
    finally:
        db.close()

    if base_count != 105:
        raise RuntimeError(f"Expected 105 baseline items, got {base_count}")
    if reinforcement_count != 35:
        raise RuntimeError(f"Expected 35 approved reinforcement items, got {reinforcement_count}")
    if total != 125:
        raise RuntimeError(f"Expected 125 total approved runtime items, got {total}")
    if v2_marked != 125:
        raise RuntimeError(f"Expected Student Experience v2 on 125 items, got {v2_marked}")
    if pretest_marked != 30:
        raise RuntimeError(f"Expected {PRETEST_VERSION} on 30 pretest items, got {pretest_marked}")

    result = {
        "baseline_items": base_count,
        "reinforcement_items": reinforcement_count,
        "total_items": total,
        "v1_additions_created": v1_created,
        "v2_additions_created": v2_created,
        "choice_corrections_created": choice_corrections_created,
        "student_experience_v2_changes": student_experience_changes,
        "student_experience_v2_items": v2_marked,
        "pretest_experience_changes": pretest_experience_changes,
        "pretest_experience_items": pretest_marked,
        "additions_created": v1_created + v2_created,
    }
    print(f"Himma full content seed OK: {result}")
    return result


if __name__ == "__main__":
    run_seed_all()
