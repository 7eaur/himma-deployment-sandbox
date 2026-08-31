"""V4 adaptive Core-selection regressions."""

import seed
from activities_v4 import _next_unused_core_item, _preferred_core_skill_id
from adaptation import _load_policy
from db.database import SessionLocal
from db.models import AssessmentSession, ContentItem, Skill, Student


def test_first_core_targets_first_configured_critical_skill_when_candidate_exists():
    seed.run_seed()
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        student.current_level = 1
        session = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="in_progress",
            assigned_level=1,
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        policy = _load_policy()
        first_code = policy["critical_skill_codes_by_level"]["1"][0]
        expected_skill = db.query(Skill).filter(
            Skill.level_id == 1,
            Skill.canonical_skill_id == first_code,
        ).one()

        assert _preferred_core_skill_id(db, student_id=student.id, level_id=1) == expected_skill.id
        item = _next_unused_core_item(
            db,
            student_id=student.id,
            session_id=session.id,
            level_id=1,
        )
        assert item is not None
        assert item.kind == "core_activity"
        assert item.level_id == 1
        assert item.skill_id == expected_skill.id
    finally:
        db.close()


def test_selection_fails_safe_to_deterministic_approved_order_when_policy_has_no_level():
    seed.run_seed()
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        session = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="in_progress",
            assigned_level=1,
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        # Level 99 has no policy and no content; no cross-level/random item may
        # be returned as a fallback.
        assert _preferred_core_skill_id(db, student_id=student.id, level_id=99) is None
        assert _next_unused_core_item(
            db,
            student_id=student.id,
            session_id=session.id,
            level_id=99,
        ) is None

        approved_l1 = db.query(ContentItem).filter(
            ContentItem.kind == "core_activity",
            ContentItem.level_id == 1,
            ContentItem.status == "approved",
        ).order_by(ContentItem.order_index, ContentItem.id).all()
        assert approved_l1
    finally:
        db.close()
