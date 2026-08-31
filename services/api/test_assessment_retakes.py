"""R3 regression coverage for durable pre/post retakes."""

from datetime import datetime, timezone
from decimal import Decimal

from assessment_retake import mark_official_completed_attempt
from db.database import SessionLocal
from db.models import (
    AssessmentRetakeAuthorization,
    AssessmentSession,
    Student,
)


def _student() -> Student:
    db = SessionLocal()
    try:
        return db.query(Student).filter(Student.access_code == "STU001").one()
    finally:
        db.close()


def _completed_assessment(
    session_type: str = "pretest",
    *,
    attempt_no: int = 1,
    score: Decimal = Decimal("60"),
    official: bool = True,
) -> int:
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        session = AssessmentSession(
            student_id=student.id,
            session_type=session_type,
            status="completed",
            completed_at=datetime.now(timezone.utc),
            final_score=score,
            assigned_level=2,
            assessment_attempt_no=attempt_no,
            official_for_reporting=official,
        )
        db.add(session)
        db.commit()
        return session.id
    finally:
        db.close()


def _login_student(client):
    response = client.post("/auth/student-login", json={"access_code": "STU001"})
    assert response.status_code == 200


def _login_supervisor(client):
    response = client.post(
        "/auth/login",
        json={
            "username": "researcher1",
            "password": "test-only-researcher-password",
        },
    )
    assert response.status_code == 200


def test_completed_pretest_cannot_restart_without_supervisor_authorization(client):
    _completed_assessment("pretest")
    _login_student(client)

    response = client.post("/assessment/start", json={"session_type": "pretest"})

    assert response.status_code == 409
    assert "إذن إعادة" in response.json()["detail"]


def test_supervisor_authorizes_retake_with_reason_and_student_consumes_it(client):
    first_id = _completed_assessment("pretest", attempt_no=1, official=True)
    student = _student()

    _login_supervisor(client)
    authorized = client.post(
        f"/researcher/students/{student.id}/assessment-retakes",
        json={"session_type": "pretest", "reason": "إعادة القياس بعد ظرف تقني موثق"},
    )
    assert authorized.status_code == 200, authorized.text
    authorization_id = authorized.json()["id"]
    assert authorized.json()["previous_session_id"] == first_id
    assert authorized.json()["status"] == "pending"

    _login_student(client)
    started = client.post("/assessment/start", json={"session_type": "pretest"})
    assert started.status_code == 200, started.text
    second_id = started.json()["id"]
    assert second_id != first_id

    db = SessionLocal()
    try:
        first = db.query(AssessmentSession).filter(AssessmentSession.id == first_id).one()
        second = db.query(AssessmentSession).filter(AssessmentSession.id == second_id).one()
        authorization = db.query(AssessmentRetakeAuthorization).filter(
            AssessmentRetakeAuthorization.id == authorization_id
        ).one()
        assert first.status == "completed"
        assert first.assessment_attempt_no == 1
        assert second.status == "in_progress"
        assert second.assessment_attempt_no == 2
        assert second.supersedes_session_id == first.id
        assert second.official_for_reporting is False
        assert authorization.status == "consumed"
        assert authorization.new_session_id == second.id
        assert authorization.consumed_at is not None
    finally:
        db.close()


def test_supervisor_cannot_authorize_retake_before_completed_attempt(client):
    student = _student()
    _login_supervisor(client)

    response = client.post(
        f"/researcher/students/{student.id}/assessment-retakes",
        json={"session_type": "pretest", "reason": "طلب إعادة قبل وجود قياس"},
    )

    assert response.status_code == 409
    assert "لا توجد محاولة مكتملة" in response.json()["detail"]


def test_active_session_blocks_retake_authorization(client):
    _completed_assessment("pretest")
    student = _student()
    db = SessionLocal()
    try:
        db.add(AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="in_progress",
            assigned_level=2,
        ))
        db.commit()
    finally:
        db.close()

    _login_supervisor(client)
    response = client.post(
        f"/researcher/students/{student.id}/assessment-retakes",
        json={"session_type": "pretest", "reason": "إعادة بعد انتهاء الجلسة الحالية"},
    )

    assert response.status_code == 409
    assert "الجلسة الحالية" in response.json()["detail"]


def test_attempt_history_preserves_initial_and_retake(client):
    first_id = _completed_assessment("pretest", attempt_no=1, score=Decimal("55"), official=False)
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        second = AssessmentSession(
            student_id=student.id,
            session_type="pretest",
            status="completed",
            completed_at=datetime.now(timezone.utc),
            final_score=Decimal("78"),
            assigned_level=2,
            assessment_attempt_no=2,
            supersedes_session_id=first_id,
            official_for_reporting=True,
        )
        db.add(second)
        db.commit()
        second_id = second.id
        student_id = student.id
    finally:
        db.close()

    _login_supervisor(client)
    response = client.get(f"/researcher/students/{student_id}/assessment-attempts")
    assert response.status_code == 200, response.text
    rows = [row for row in response.json() if row["session_type"] == "pretest"]
    assert [row["id"] for row in rows] == [first_id, second_id]
    assert [row["attempt_no"] for row in rows] == [1, 2]
    assert rows[0]["official_for_reporting"] is False
    assert rows[1]["official_for_reporting"] is True
    assert rows[1]["supersedes_session_id"] == first_id


def test_completed_retake_becomes_only_official_attempt_without_deleting_history():
    first_id = _completed_assessment("pretest", attempt_no=1, official=True)
    db = SessionLocal()
    try:
        first = db.query(AssessmentSession).filter(AssessmentSession.id == first_id).one()
        second = AssessmentSession(
            student_id=first.student_id,
            session_type="pretest",
            status="completed",
            completed_at=datetime.now(timezone.utc),
            final_score=Decimal("82"),
            assigned_level=3,
            assessment_attempt_no=2,
            supersedes_session_id=first.id,
            official_for_reporting=False,
        )
        db.add(second)
        db.flush()
        second_id = second.id

        mark_official_completed_attempt(db, second)
        db.commit()

        first = db.query(AssessmentSession).filter(AssessmentSession.id == first_id).one()
        second = db.query(AssessmentSession).filter(AssessmentSession.id == second_id).one()
        assert first.official_for_reporting is False
        assert second.official_for_reporting is True
        assert db.query(AssessmentSession).filter(
            AssessmentSession.student_id == first.student_id,
            AssessmentSession.session_type == "pretest",
        ).count() == 2
    finally:
        db.close()


def test_partial_attempt_uniqueness_does_not_block_multiple_level_core_sessions():
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        first = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="completed",
            assigned_level=1,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(first)
        db.flush()
        second = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="in_progress",
            assigned_level=2,
        )
        db.add(second)
        db.commit()
        assert first.assessment_attempt_no == 1
        assert second.assessment_attempt_no == 1
        assert first.id != second.id
    finally:
        db.close()
