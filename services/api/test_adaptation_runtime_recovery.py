"""Recovery regressions for the adaptive reinforcement lifecycle."""

from datetime import datetime, timezone

import adaptation_runtime
import seed
from conftest import TestingSessionLocal
from db.adaptation_models import AdaptationDecision
from db.models import AssessmentSession, Attempt, ContentItem, Student


def test_completed_reinforcement_is_fulfilled_not_a_new_mapping_gap(monkeypatch):
    """Once approved reinforcement is completed, the path must be able to finish."""
    seed.run_seed()
    db = TestingSessionLocal()
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

    core_items = (
        db.query(ContentItem)
        .filter(ContentItem.kind == "core_activity", ContentItem.level_id == 1)
        .order_by(ContentItem.order_index)
        .all()
    )
    assert len(core_items) == 10
    for item in core_items:
        db.add(Attempt(
            session_id=session.id,
            item_id=item.id,
            status="completed",
            completed_at=datetime.now(timezone.utc),
        ))

    reinforcement = (
        db.query(ContentItem)
        .filter(ContentItem.kind == "reinforcement_activity", ContentItem.level_id == 1)
        .order_by(ContentItem.order_index)
        .first()
    )
    assert reinforcement is not None
    db.add(Attempt(
        session_id=session.id,
        item_id=reinforcement.id,
        status="completed",
        completed_at=datetime.now(timezone.utc),
    ))

    decision = AdaptationDecision(
        student_id=student.id,
        decision_source="automatic",
        action="support",
        mastery_score=40,
        previous_level=1,
        new_level=1,
        weakest_skill_id=reinforcement.skill_id,
        recommended_item_id=reinforcement.id,
        valid_attempt_count=10,
        consecutive_low_count=1,
        snapshot_key="recovery:completed:reinforcement",
        explanation={
            "reason": "low_mastery_support_first",
            "mapping_gap": "no_approved_reinforcement_selected_for_weakest_skill",
        },
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)

    monkeypatch.setattr(
        adaptation_runtime,
        "evaluate_student",
        lambda _db, _student, session_id=None: {
            "ready": True,
            "decision_id": decision.id,
            "action": "support",
            "recommended_item_id": reinforcement.id,
            "explanation": decision.explanation,
            "evidence_scope_session_id": session_id,
        },
    )

    result = adaptation_runtime.prepare_next_for_student(db, student, session)

    assert result["mapping_blocked"] is False
    assert result["recommendation_fulfilled"] is True
    db.refresh(decision)
    assert decision.explanation.get("reinforcement_fulfilled") is True
    assert "mapping_gap" not in decision.explanation
    db.close()
