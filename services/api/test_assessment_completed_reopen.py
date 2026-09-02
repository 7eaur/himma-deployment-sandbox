"""Regression coverage for reopening an already completed assessment session."""

from datetime import datetime, timezone
from decimal import Decimal

from conftest import TestingSessionLocal
from db.models import AssessmentSession, Student


def _completed_session(*, final_score=Decimal("73.5000"), assigned_level=2) -> tuple[int, datetime]:
    db = TestingSessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        completed_at = datetime.now(timezone.utc)
        session = AssessmentSession(
            student_id=student.id,
            session_type="pretest",
            status="completed",
            final_score=final_score,
            assigned_level=assigned_level,
            completed_at=completed_at,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session.id, session.completed_at
    finally:
        db.close()


def test_completed_assessment_reopen_returns_no_next_and_replays_stored_result(student_client):
    session_id, completed_at = _completed_session()

    next_response = student_client.get(f"/assessment-view/session/{session_id}/next")
    assert next_response.status_code == 200
    assert next_response.json() is None

    finish_response = student_client.post(f"/assessment/session/{session_id}/finish")
    assert finish_response.status_code == 200
    payload = finish_response.json()
    assert payload["id"] == session_id
    assert Decimal(str(payload["final_score"])) == Decimal("73.5000")
    assert payload["assigned_level"] == 2

    db = TestingSessionLocal()
    try:
        session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).one()
        assert session.status == "completed"
        assert session.completed_at == completed_at
        assert session.final_score == Decimal("73.5000")
        assert session.assigned_level == 2
    finally:
        db.close()


def test_completed_assessment_without_persisted_result_is_not_fabricated(student_client):
    session_id, _ = _completed_session(final_score=None, assigned_level=None)

    next_response = student_client.get(f"/assessment-view/session/{session_id}/next")
    assert next_response.status_code == 200
    assert next_response.json() is None

    finish_response = student_client.post(f"/assessment/session/{session_id}/finish")
    assert finish_response.status_code == 409
    assert finish_response.json()["detail"] == "نتيجة الجلسة المكتملة غير متاحة"
