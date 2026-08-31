"""Supervisor fallback for approved reinforcement when exact mapping is unavailable."""

import seed
from conftest import TestingSessionLocal
from db.adaptation_models import AdaptationDecision
from db.models import AssessmentSession, Attempt, AuditLog, Student


def _create_mapping_gap():
    seed.run_seed()
    db = TestingSessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    session = AssessmentSession(
        student_id=student.id,
        session_type="core",
        status="in_progress",
        assigned_level=1,
    )
    db.add(session)
    db.flush()
    decision = AdaptationDecision(
        student_id=student.id,
        decision_source="automatic",
        action="support",
        mastery_score=35,
        previous_level=1,
        new_level=1,
        weakest_skill_id=None,
        recommended_item_id=None,
        valid_attempt_count=10,
        consecutive_low_count=1,
        snapshot_key="review-gap-1",
        explanation={
            "reason": "low_mastery_support_first",
            "mapping_gap": "no_approved_reinforcement_selected_for_weakest_skill",
        },
    )
    db.add(decision)
    db.commit()
    values = student.id, session.id, decision.id
    db.close()
    return values


def test_supervisor_can_choose_only_approved_same_level_reinforcement(researcher_client):
    student_id, session_id, automatic_decision_id = _create_mapping_gap()

    options_response = researcher_client.get(
        f"/researcher/students/{student_id}/adaptation/reinforcement-options"
    )
    assert options_response.status_code == 200
    payload = options_response.json()
    assert payload["level_id"] == 1
    assert len(payload["options"]) == 5
    assert all(option["already_used"] is False for option in payload["options"])

    selected = payload["options"][0]
    assigned = researcher_client.post(
        f"/researcher/students/{student_id}/adaptation/assign-reinforcement",
        json={
            "item_id": selected["item_id"],
            "reason": "اختيار موثق بعد مراجعة أداء الطالب",
        },
    )
    assert assigned.status_code == 200
    assert assigned.json()["item_id"] == selected["item_id"]

    db = TestingSessionLocal()
    attempt = db.query(Attempt).filter(
        Attempt.session_id == session_id,
        Attempt.item_id == selected["item_id"],
    ).one()
    assert attempt.status == "in_progress"

    automatic = db.query(AdaptationDecision).filter(
        AdaptationDecision.id == automatic_decision_id
    ).one()
    assert automatic.recommended_item_id == selected["item_id"]
    assert "mapping_gap" not in automatic.explanation
    assert automatic.explanation["manual_reinforcement_resolution"]["item_id"] == selected["item_id"]

    manual = db.query(AdaptationDecision).filter(
        AdaptationDecision.student_id == student_id,
        AdaptationDecision.decision_source == "manual",
        AdaptationDecision.recommended_item_id == selected["item_id"],
    ).one()
    assert manual.manual_reason == "اختيار موثق بعد مراجعة أداء الطالب"
    assert manual.explanation["reason"] == "supervisor_reinforcement_assignment"

    audit = db.query(AuditLog).filter(
        AuditLog.action == "adaptation.reinforcement.assign",
        AuditLog.entity_id == str(student_id),
    ).one()
    assert audit.actor_role == "researcher"
    db.close()


def test_reinforcement_resolution_requires_real_pending_gap(researcher_client):
    seed.run_seed()
    db = TestingSessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    session = AssessmentSession(
        student_id=student.id,
        session_type="core",
        status="in_progress",
        assigned_level=1,
    )
    db.add(session)
    db.commit()
    student_id = student.id
    db.close()

    response = researcher_client.get(
        f"/researcher/students/{student_id}/adaptation/reinforcement-options"
    )
    assert response.status_code == 409
    assert "لا توجد فجوة تقوية معلقة" in response.json()["detail"]
