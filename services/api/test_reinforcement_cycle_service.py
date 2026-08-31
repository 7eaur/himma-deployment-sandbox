"""Service-level M03 tests for reinforcement → verification lifecycle."""

import seed
from db.activity_models import ActivityStepResponse
from db.adaptation_models import AdaptationDecision
from db.database import SessionLocal
from db.models import AssessmentSession, Attempt, ContentItem, Student
from reinforcement_cycles import ensure_cycle, finish_verification_step, mark_reinforcement_completed


def _setup_cycle_fixture(db):
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    student.current_level = 1
    session = AssessmentSession(student_id=student.id, session_type="core", status="in_progress", assigned_level=1)
    db.add(session)
    db.flush()

    core = db.query(ContentItem).filter(
        ContentItem.kind == "core_activity", ContentItem.level_id == 1
    ).order_by(ContentItem.order_index).first()
    reinforcement = db.query(ContentItem).filter(
        ContentItem.kind == "reinforcement_activity", ContentItem.level_id == 1
    ).order_by(ContentItem.order_index).first()
    source = Attempt(session_id=session.id, item_id=core.id, status="completed")
    db.add(source)
    db.flush()
    step = core.steps[0]
    db.add(ActivityStepResponse(
        attempt_id=source.id,
        step_id=step.id,
        attempt_no=1,
        response_payload={"selected_option_ids": [999]},
        is_correct=False,
        hint_used=False,
        elapsed_seconds=1,
    ))
    decision = AdaptationDecision(
        student_id=student.id,
        decision_source="automatic",
        action="support",
        mastery_score=0,
        previous_level=1,
        new_level=1,
        weakest_skill_id=core.skill_id,
        recommended_item_id=reinforcement.id,
        valid_attempt_count=1,
        consecutive_low_count=0,
        snapshot_key=f"immediate:{source.id}",
        explanation={"source_attempt_id": source.id, "reason": "activity_below_reinforcement_threshold"},
    )
    db.add(decision)
    db.flush()
    reinforcement_attempt = Attempt(session_id=session.id, item_id=reinforcement.id, status="in_progress")
    db.add(reinforcement_attempt)
    db.flush()
    return student, session, source, step, decision, reinforcement, reinforcement_attempt


def test_cycle_records_failed_source_and_reopens_it_only_after_reinforcement_completion():
    seed.run_seed()
    db = SessionLocal()
    try:
        student, session, source, step, decision, reinforcement, reinforcement_attempt = _setup_cycle_fixture(db)
        cycle = ensure_cycle(
            db,
            student=student,
            session_id=session.id,
            decision=decision,
            reinforcement_attempt_id=reinforcement_attempt.id,
        )
        assert cycle is not None
        assert cycle.source_step_ids == [step.id]
        assert cycle.status == "reinforcement_in_progress"

        assert mark_reinforcement_completed(db, cycle=cycle) is None
        assert source.status == "completed"

        reinforcement_attempt.status = "completed"
        db.flush()
        reopened = mark_reinforcement_completed(db, cycle=cycle)
        assert reopened is not None
        assert reopened.id == source.id
        assert source.status == "in_progress"
        assert cycle.status == "verification_pending"
    finally:
        db.close()


def test_verification_is_bounded_and_escalates_after_two_failed_rounds():
    seed.run_seed()
    db = SessionLocal()
    try:
        student, session, source, step, decision, reinforcement, reinforcement_attempt = _setup_cycle_fixture(db)
        cycle = ensure_cycle(
            db,
            student=student,
            session_id=session.id,
            decision=decision,
            reinforcement_attempt_id=reinforcement_attempt.id,
        )
        reinforcement_attempt.status = "completed"
        db.flush()
        mark_reinforcement_completed(db, cycle=cycle)

        assert finish_verification_step(db, cycle=cycle, step_id=step.id, is_correct=False) == "verification_pending"
        assert cycle.verification_round == 1
        assert finish_verification_step(db, cycle=cycle, step_id=step.id, is_correct=False) == "escalated"
        assert cycle.verification_round == 2
        assert cycle.escalation_reason == "verification_failed_after_bounded_retries"
    finally:
        db.close()
