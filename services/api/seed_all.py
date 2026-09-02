"""Seed the complete currently approved Himma runtime content set."""
from __future__ import annotations

import json
from pathlib import Path

import seed
import seed_reinforcement_additions
import seed_reinforcement_additions_v2
import seed_student_choice_corrections
import seed_student_experience_v2
import seed_l1_auditory_story_replacement
import seed_pretest_experience_2026_09_01
import seed_db_runtime_contract
import seed_learning_posttest_projection_runtime
from db.database import SessionLocal
from db.models import ContentItem

ROOT = Path(__file__).resolve().parents[2]
BASE_CATALOG = ROOT / "packages" / "content" / "src" / "catalog.json"
PRETEST_VERSION = "HIMMA-PRETEST-2026-09-01"
LEARNING_VERSION = seed_learning_posttest_projection_runtime.LEARNING_VERSION
POSTTEST_VERSION = seed_learning_posttest_projection_runtime.POSTTEST_VERSION
DB_RUNTIME_VERSION = seed_db_runtime_contract.VERSION


def _base_stable_keys() -> set[str]:
    payload = json.loads(BASE_CATALOG.read_text(encoding="utf-8"))
    return {str(item["stable_key"]) for item in payload["items"]}


def _base_is_complete() -> bool:
    required = _base_stable_keys()
    db = SessionLocal()
    try:
        present = {row[0] for row in db.query(ContentItem.stable_key).filter(ContentItem.stable_key.in_(required)).all()}
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
    auditory_story_changes = seed_l1_auditory_story_replacement.run_seed()
    pretest_experience_changes = seed_pretest_experience_2026_09_01.run_seed()

    # Source files are allowed only in the import pipeline. Snapshot all source,
    # media semantics and media gaps into PostgreSQL before runtime projection.
    db_runtime_changes = seed_db_runtime_contract.run_seed()
    auditory_runtime_changes = seed_l1_auditory_story_replacement.patch_db_runtime()
    projection_result = seed_learning_posttest_projection_runtime.run_seed()

    db = SessionLocal()
    try:
        all_items = db.query(ContentItem).all()
        total = len(all_items)
        base_count = db.query(ContentItem).filter(ContentItem.stable_key.in_(_base_stable_keys())).count()
        reinforcement_count = db.query(ContentItem).filter(ContentItem.kind == "reinforcement_activity").count()
        v2_marked = sum(1 for item in all_items if (item.template_data or {}).get("student_experience_version") == "HIMMA-STUDENT-EXPERIENCE-2.0")
        pretest_marked = sum(1 for item in all_items if item.kind == "pretest_question" and (item.template_data or {}).get("pretest_experience_version") == PRETEST_VERSION)
        learning_marked = sum(1 for item in all_items if item.kind in {"core_activity", "reinforcement_activity"} and (item.template_data or {}).get("learning_experience_version") == LEARNING_VERSION)
        posttest_marked = sum(1 for item in all_items if item.kind == "posttest_question" and (item.template_data or {}).get("posttest_experience_version") == POSTTEST_VERSION)
        db_runtime_marked = sum(1 for item in all_items if ((item.template_data or {}).get("db_runtime") or {}).get("version") == DB_RUNTIME_VERSION)
    finally:
        db.close()

    if base_count != 105: raise RuntimeError(f"Expected 105 baseline items, got {base_count}")
    if reinforcement_count != 35: raise RuntimeError(f"Expected 35 approved reinforcement items, got {reinforcement_count}")
    if total != 125: raise RuntimeError(f"Expected 125 total approved runtime items, got {total}")
    if v2_marked != 125: raise RuntimeError(f"Expected Student Experience v2 on 125 items, got {v2_marked}")
    if pretest_marked != 30: raise RuntimeError(f"Expected {PRETEST_VERSION} on 30 pretest items, got {pretest_marked}")
    if learning_marked != 65: raise RuntimeError(f"Expected {LEARNING_VERSION} on 65 learning items, got {learning_marked}")
    if posttest_marked != 30: raise RuntimeError(f"Expected {POSTTEST_VERSION} on 30 posttest items, got {posttest_marked}")
    if db_runtime_marked != 125: raise RuntimeError(f"Expected {DB_RUNTIME_VERSION} on 125 items, got {db_runtime_marked}")

    result = {
        "baseline_items": base_count, "reinforcement_items": reinforcement_count, "total_items": total,
        "v1_additions_created": v1_created, "v2_additions_created": v2_created,
        "choice_corrections_created": choice_corrections_created,
        "student_experience_v2_changes": student_experience_changes, "student_experience_v2_items": v2_marked,
        "auditory_story_changes": auditory_story_changes,
        "pretest_experience_changes": pretest_experience_changes, "pretest_experience_items": pretest_marked,
        "db_runtime_changes": db_runtime_changes, "auditory_runtime_changes": auditory_runtime_changes, "db_runtime_items": db_runtime_marked,
        "learning_experience_changes": projection_result["learning_changed"], "learning_experience_items": learning_marked,
        "posttest_experience_changes": projection_result["posttest_changed"], "posttest_experience_items": posttest_marked,
        "additions_created": v1_created + v2_created,
    }
    print(f"Himma full content seed OK: {result}")
    return result


if __name__ == "__main__":
    run_seed_all()
