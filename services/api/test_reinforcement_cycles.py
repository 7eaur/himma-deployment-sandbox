"""Durability constraints for the M03 reinforcement verification cycle."""

import seed
from db.adaptation_models import AdaptationDecision
from db.database import SessionLocal
from db.models import AssessmentSession, Attempt, ContentItem, Student
from db.reinforcement_models import ReinforcementCycle


def test_reinforcement_cycle_persists_source_and_target_without_relabelling_history():
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
        db.flush()

        core = db.query(ContentItem).filter(
            ContentItem.kind == "core_activity",
            ContentItem.level_id == 1,
        ).order_by(ContentItem.order_index).first()
        reinforcement = db.query(ContentItem).filter(
            ContentItem.kind == "reinforcement_activity",
            ContentItem.level_id == 1,
        ).order_by(ContentItem.order_index).first()
        source_attempt = Attempt(session_id=session.id, item_id=core.id, status="completed")
        db.add(source_attempt)
        db.flush()

        decision = AdaptationDecision(
            student_id=student.id,
            decision_source="automatic",
            action="support",
            mastery_score=50,
            previous_level=1,
            new_level=1,
            weakest_skill_id=core.skill_id,
            recommended_item_id=reinforcement.id,
            valid_attempt_count=1,
            consecutive_low_count=0,
            snapshot_key="cycle-model-test",
            explanation={"reason": "test"},
        )
        db.add(decision)
        db.flush()

        cycle = ReinforcementCycle(
            student_id=student.id,
            session_id=session.id,
            decision_id=decision.id,
            source_attempt_id=source_attempt.id,
            source_step_ids=[core.steps[0].id],
            reinforcement_item_id=reinforcement.id,
            status="reinforcement_pending",
        )
        db.add(cycle)
        db.commit()
        db.refresh(cycle)

        assert cycle.source_attempt_id == source_attempt.id
        assert cycle.reinforcement_item_id == reinforcement.id
        assert cycle.status == "reinforcement_pending"
        assert cycle.verification_round == 0
        assert cycle.max_verification_rounds == 2
        assert session.assigned_level == 1
    finally:
        db.close()
