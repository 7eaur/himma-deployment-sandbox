"""End-to-end backend contract for the M03 remediation loop.

This test deliberately stays below the HTTP/UI layer. It proves that the
complete approved runtime catalog can seed, a concrete failed core step can be
mapped to an approved same-level reinforcement, completion reopens the exact
source attempt for verification, and successful verification closes the cycle.
"""

from datetime import datetime, timezone

import seed_all
from conftest import TestingSessionLocal
from db.activity_models import ActivityStepResponse
from db.adaptation_models import AdaptationDecision
from db.models import AssessmentSession, Attempt, ContentItem, Skill, Student
from reinforcement_cycles import (
    ensure_cycle,
    finish_verification_step,
    mark_reinforcement_completed,
)


def _canonical_item(db, canonical_id: str) -> ContentItem:
    for item in db.query(ContentItem).all():
        if (item.template_data or {}).get("canonical_id") == canonical_id:
            return item
    raise AssertionError(f"Missing seeded content item {canonical_id}")


def test_failed_core_to_reinforcement_to_verified_return_path():
    seeded = seed_all.run_seed_all()
    assert seeded["baseline_items"] == 105
    assert seeded["reinforcement_items"] == 35
    assert seeded["total_items"] == 125

    db = TestingSessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        student.current_level = 2

        skill = db.query(Skill).filter(
            Skill.level_id == 2,
            Skill.canonical_skill_id == "shadda_word_reading",
        ).one()
        source_item = db.query(ContentItem).filter(
            ContentItem.level_id == 2,
            ContentItem.kind == "core_activity",
            ContentItem.skill_id == skill.id,
        ).order_by(ContentItem.order_index).first()
        assert source_item is not None
        assert source_item.steps

        reinforcement = _canonical_item(db, "L2-REIN-09")
        assert reinforcement.kind == "reinforcement_activity"
        assert reinforcement.level_id == 2
        assert reinforcement.status == "approved"

        session = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="in_progress",
            assigned_level=2,
        )
        db.add(session)
        db.flush()

        source_attempt = Attempt(
            session_id=session.id,
            item_id=source_item.id,
            status="completed",
            completed_at=datetime.now(timezone.utc),
        )
        db.add(source_attempt)
        db.flush()

        failed_step = source_item.steps[0]
        db.add(ActivityStepResponse(
            attempt_id=source_attempt.id,
            step_id=failed_step.id,
            attempt_no=1,
            response_payload={"selected_option_ids": []},
            is_correct=False,
            hint_used=False,
            elapsed_seconds=4,
        ))

        decision = AdaptationDecision(
            student_id=student.id,
            decision_source="automatic",
            action="support",
            mastery_score=40,
            previous_level=2,
            new_level=2,
            weakest_skill_id=skill.id,
            recommended_item_id=reinforcement.id,
            valid_attempt_count=1,
            consecutive_low_count=1,
            snapshot_key=f"m03:e2e:{source_attempt.id}",
            explanation={
                "reason": "activity_below_reinforcement_threshold",
                "source_attempt_id": source_attempt.id,
            },
        )
        db.add(decision)
        db.flush()

        reinforcement_attempt = Attempt(
            session_id=session.id,
            item_id=reinforcement.id,
            status="in_progress",
        )
        db.add(reinforcement_attempt)
        db.flush()

        cycle = ensure_cycle(
            db,
            student=student,
            session_id=session.id,
            decision=decision,
            reinforcement_attempt_id=reinforcement_attempt.id,
        )
        assert cycle is not None
        assert cycle.status == "reinforcement_in_progress"
        assert cycle.source_attempt_id == source_attempt.id
        assert cycle.source_step_ids == [failed_step.id]
        assert cycle.reinforcement_item_id == reinforcement.id

        reinforcement_attempt.status = "completed"
        reinforcement_attempt.completed_at = datetime.now(timezone.utc)
        reopened = mark_reinforcement_completed(db, cycle=cycle)
        assert reopened is not None
        assert reopened.id == source_attempt.id
        assert reopened.status == "in_progress"
        assert cycle.status == "verification_pending"

        db.add(ActivityStepResponse(
            attempt_id=source_attempt.id,
            step_id=failed_step.id,
            attempt_no=2,
            response_payload={
                "reinforcement_cycle_id": cycle.id,
                "reinforcement_verification": True,
                "selected_option_ids": [],
            },
            is_correct=True,
            hint_used=False,
            elapsed_seconds=3,
        ))
        db.flush()

        status = finish_verification_step(
            db,
            cycle=cycle,
            step_id=failed_step.id,
            is_correct=True,
        )
        assert status == "verified"
        assert cycle.status == "verified"
        assert cycle.completed_at is not None
        assert cycle.escalation_reason is None
    finally:
        db.close()
