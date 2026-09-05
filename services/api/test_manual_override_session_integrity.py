"""Manual adaptation override integrity scenarios."""

from datetime import datetime, timezone

import seed
from conftest import TestingSessionLocal
from db.models import (
    AssessmentSession,
    Attempt,
    AttemptResponse,
    AudioSubmission,
    ContentItem,
    Student,
)
from journey import build_journey_summary


def test_manual_override_transitions_active_core_session_and_preserves_history(researcher_client):
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
    item = (
        db.query(ContentItem)
        .filter(ContentItem.kind == "core_activity", ContentItem.level_id == 1)
        .order_by(ContentItem.order_index)
        .first()
    )
    attempt = Attempt(
        session_id=session.id,
        item_id=item.id,
        status="completed",
        completed_at=datetime.now(timezone.utc),
    )
    db.add(attempt)
    db.commit()
    student_id = student.id
    old_session_id = session.id
    attempt_id = attempt.id
    db.close()

    response = researcher_client.post(
        f"/researcher/students/{student_id}/adaptation/manual-override",
        json={"new_level": 2, "reason": "تعديل مستوى موثق لاختبار سلامة المسار"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["previous_level"] == 1
    assert payload["new_level"] == 2
    assert payload["explanation"]["manual_session_transition"] is True
    assert payload["explanation"]["previous_session_id"] == old_session_id

    db = TestingSessionLocal()
    try:
        student = db.query(Student).filter(Student.id == student_id).one()
        old_session = db.query(AssessmentSession).filter(AssessmentSession.id == old_session_id).one()
        preserved_attempt = db.query(Attempt).filter(Attempt.id == attempt_id).one()
        active = db.query(AssessmentSession).filter(
            AssessmentSession.student_id == student_id,
            AssessmentSession.status == "in_progress",
        ).one()

        assert student.current_level == 2
        assert old_session.status == "completed"
        assert old_session.assigned_level == 1
        assert preserved_attempt.session_id == old_session_id
        assert active.session_type == "core"
        assert active.assigned_level == 2
        assert active.id == payload["explanation"]["next_session_id"]
    finally:
        db.close()


def test_manual_override_is_rejected_while_assessment_is_active(researcher_client):
    seed.run_seed()
    db = TestingSessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    student.current_level = 1
    db.add(AssessmentSession(
        student_id=student.id,
        session_type="pretest",
        status="in_progress",
        assigned_level=1,
    ))
    db.commit()
    student_id = student.id
    db.close()

    response = researcher_client.post(
        f"/researcher/students/{student_id}/adaptation/manual-override",
        json={"new_level": 2, "reason": "محاولة تغيير أثناء اختبار نشط"},
    )
    assert response.status_code == 409
    assert "اختبار نشط" in response.json()["detail"]


def test_reopening_learning_after_completed_l3_resets_posttest_and_overrides_historical_completion(
    researcher_client,
):
    """A reopened learning path must beat an older completed L3 in current state."""
    seed.run_seed()
    db = TestingSessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        student.current_level = 3
        student.posttest_enabled = True
        now = datetime.now(timezone.utc)

        pretest = AssessmentSession(
            student_id=student.id,
            session_type="pretest",
            status="completed",
            assigned_level=3,
            completed_at=now,
        )
        db.add(pretest)
        db.flush()

        l3_session = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="completed",
            assigned_level=3,
            completed_at=now,
        )
        db.add(l3_session)
        db.flush()

        items = (
            db.query(ContentItem)
            .filter(ContentItem.kind == "core_activity", ContentItem.level_id == 3)
            .order_by(ContentItem.order_index, ContentItem.id)
            .all()
        )
        assert len(items) == 10
        for item in items:
            db.add(Attempt(
                session_id=l3_session.id,
                item_id=item.id,
                status="completed",
                completed_at=now,
            ))
        db.commit()
        student_id = student.id
        historical_l3_session_id = l3_session.id
        historical_attempt_ids = {
            row[0]
            for row in db.query(Attempt.id).filter(Attempt.session_id == historical_l3_session_id).all()
        }

        before = build_journey_summary(db, student)
        assert before["learning_journey_completed"] is True
        assert before["posttest_ready"] is True
    finally:
        db.close()

    response = researcher_client.post(
        f"/researcher/students/{student_id}/adaptation/manual-override",
        json={"new_level": 2, "reason": "إعادة فتح تعلم موثقة لمعالجة حاجة تعليمية جديدة"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["previous_level"] == 3
    assert payload["new_level"] == 2
    assert payload["explanation"]["learning_reopened"] is True
    assert payload["explanation"]["posttest_access_reset"] is True

    db = TestingSessionLocal()
    try:
        student = db.query(Student).filter(Student.id == student_id).one()
        historical_l3 = db.query(AssessmentSession).filter(
            AssessmentSession.id == historical_l3_session_id,
        ).one()
        active_l2 = db.query(AssessmentSession).filter(
            AssessmentSession.student_id == student_id,
            AssessmentSession.session_type == "core",
            AssessmentSession.status == "in_progress",
        ).one()
        preserved_attempt_ids = {
            row[0]
            for row in db.query(Attempt.id).filter(Attempt.session_id == historical_l3_session_id).all()
        }

        assert student.current_level == 2
        assert student.posttest_enabled is False
        assert historical_l3.status == "completed"
        assert historical_l3.assigned_level == 3
        assert preserved_attempt_ids == historical_attempt_ids
        assert active_l2.assigned_level == 2
        assert active_l2.id == payload["explanation"]["next_session_id"]

        summary = build_journey_summary(db, student)
        by_level = {row["level_id"]: row for row in summary["levels"]}
        assert summary["learning_journey_completed"] is False
        assert summary["posttest_ready"] is False
        assert summary["posttest_enabled"] is False
        assert by_level[2]["state"] == "active"
        assert by_level[3]["state"] == "completed"
    finally:
        db.close()


def test_level_change_is_rejected_after_final_posttest_completion(researcher_client):
    seed.run_seed()
    db = TestingSessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    student.current_level = 3
    db.add(AssessmentSession(
        student_id=student.id,
        session_type="posttest",
        status="completed",
        assigned_level=3,
        completed_at=datetime.now(timezone.utc),
    ))
    db.commit()
    student_id = student.id
    db.close()

    response = researcher_client.post(
        f"/researcher/students/{student_id}/adaptation/manual-override",
        json={"new_level": 2, "reason": "محاولة تعديل بعد اعتماد القياس البعدي النهائي"},
    )
    assert response.status_code == 409
    assert "بعد اعتماد الاختبار البعدي النهائي" in response.json()["detail"]


def test_level_change_is_blocked_while_learning_audio_review_is_pending(researcher_client):
    seed.run_seed()
    db = TestingSessionLocal()
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
        item = (
            db.query(ContentItem)
            .filter(ContentItem.kind == "core_activity", ContentItem.level_id == 1)
            .order_by(ContentItem.order_index, ContentItem.id)
            .first()
        )
        assert item is not None and item.steps
        attempt = Attempt(session_id=session.id, item_id=item.id, status="in_progress")
        db.add(attempt)
        db.flush()
        attempt_response = AttemptResponse(
            attempt_id=attempt.id,
            step_id=item.steps[0].id,
            is_correct=None,
        )
        db.add(attempt_response)
        db.flush()
        db.add(AudioSubmission(
            response_id=attempt_response.id,
            storage_key=f"tests/manual-override/{student.id}.wav",
            file_size=128,
            mime_type="audio/wav",
            status="uploaded",
        ))
        db.commit()
        student_id = student.id
    finally:
        db.close()

    response = researcher_client.post(
        f"/researcher/students/{student_id}/adaptation/manual-override",
        json={"new_level": 2, "reason": "لا يجوز تجاوز تسجيل ينتظر المراجعة"},
    )
    assert response.status_code == 409
    assert "مراجعة الصوت" in response.json()["detail"]
