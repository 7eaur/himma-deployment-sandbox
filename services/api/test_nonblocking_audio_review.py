"""Regression coverage for the learner's asynchronous audio-review workflow."""

import schemas
import audio_review_navigation as navigation
from audio_review_navigation import next_activity_step
from conftest import TestingSessionLocal
from db.models import (
    AssessmentSession,
    Attempt,
    AttemptResponse,
    AudioSubmission,
    ContentItem,
    ContentStep,
    Skill,
    Student,
    User,
)
from review import begin_student_rerecord, get_student_audio_reviews, grade_audio_submission


def _content(db):
    skill = Skill(
        skill_key="audio-nonblocking",
        name="قراءة جهرية",
        description="test",
        level_id=1,
        canonical_skill_id="TEST-AUDIO-NONBLOCKING",
    )
    db.add(skill)
    db.flush()
    audio_item = ContentItem(
        stable_key="TEST-AUDIO-CORE-01",
        kind="core_activity",
        level_id=1,
        skill_id=skill.id,
        interaction_type="read_aloud",
        order_index=1,
        version="test",
        status="approved",
        checksum="a" * 64,
        template_data={"title": "اقرأ الجملة"},
    )
    next_item = ContentItem(
        stable_key="TEST-NEXT-CORE-02",
        kind="core_activity",
        level_id=1,
        skill_id=skill.id,
        interaction_type="choose_one",
        order_index=2,
        version="test",
        status="approved",
        checksum="b" * 64,
        template_data={"title": "النشاط التالي"},
    )
    db.add_all([audio_item, next_item])
    db.flush()
    audio_step = ContentStep(
        item_id=audio_item.id,
        order_index=1,
        prompt_text="اقرأ",
        expected_reading_text="قرأ سامر",
    )
    next_step = ContentStep(
        item_id=next_item.id,
        order_index=1,
        prompt_text="اختر",
    )
    db.add_all([audio_step, next_step])
    db.flush()
    return audio_item, audio_step, next_item


def _pending_submission(db, student, session, audio_item, audio_step):
    audio_attempt = Attempt(session_id=session.id, item_id=audio_item.id, status="completed")
    db.add(audio_attempt)
    db.flush()
    response = AttemptResponse(
        attempt_id=audio_attempt.id,
        step_id=audio_step.id,
        selected_option_id=None,
        is_correct=None,
        elapsed_seconds=2,
    )
    db.add(response)
    db.flush()
    submission = AudioSubmission(
        response_id=response.id,
        storage_key=f"audio/{student.id}/test.webm",
        file_size=100,
        mime_type="audio/webm",
        duration_seconds=2,
        status="uploaded",
    )
    db.add(submission)
    db.flush()
    return audio_attempt, submission


def test_uploaded_audio_does_not_stop_learning_and_rerecord_waits_for_dashboard_open():
    db = TestingSessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        supervisor = db.query(User).filter(User.username == "researcher1").one()
        audio_item, audio_step, next_item = _content(db)
        session = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="in_progress",
            assigned_level=1,
        )
        db.add(session)
        db.flush()
        audio_attempt = Attempt(session_id=session.id, item_id=audio_item.id, status="in_progress")
        db.add(audio_attempt)
        db.flush()
        response = AttemptResponse(
            attempt_id=audio_attempt.id,
            step_id=audio_step.id,
            selected_option_id=None,
            is_correct=None,
            elapsed_seconds=2,
        )
        db.add(response)
        db.flush()
        submission = AudioSubmission(
            response_id=response.id,
            storage_key=f"audio/{student.id}/test.webm",
            file_size=100,
            mime_type="audio/webm",
            duration_seconds=2,
            status="uploaded",
        )
        db.add(submission)
        db.commit()

        # Pending review is neutral evidence, but navigation immediately moves on.
        next_payload = next_activity_step(session.id, db=db, student=student)
        assert next_payload is not None
        assert next_payload["item"]["id"] == next_item.id
        db.refresh(audio_attempt)
        db.refresh(session)
        db.refresh(student)
        assert audio_attempt.status == "completed"
        assert session.status == "in_progress"
        assert student.current_level == 1

        # A reviewer request becomes a dashboard task; it must not reopen the old
        # attempt or interrupt the activity the learner is currently doing.
        result = grade_audio_submission(
            submission.id,
            schemas.GradeAudioRequest(is_valid=False),
            db=db,
            supervisor=supervisor,
        )
        assert result["rerecord_queued"] is True
        db.refresh(audio_attempt)
        db.refresh(submission)
        assert audio_attempt.status == "completed"
        assert submission.status == "rerecord_required"

        tasks = get_student_audio_reviews(db=db, student=student)
        rerecord = next(task for task in tasks if task["id"] == submission.id)
        assert rerecord["can_rerecord"] is True
        assert rerecord["session_id"] == session.id

        current_payload = next_activity_step(session.id, db=db, student=student)
        assert current_payload is not None
        assert current_payload["item"]["id"] == next_item.id

        # Only the student's explicit dashboard action reopens the exact recording.
        opened = begin_student_rerecord(submission.id, db=db, student=student)
        assert opened["session_id"] == session.id
        assert opened["item_id"] == audio_item.id
        db.refresh(audio_attempt)
        assert audio_attempt.status == "in_progress"

        rerecord_payload = next_activity_step(session.id, db=db, student=student)
        assert rerecord_payload is not None
        assert rerecord_payload["item"]["id"] == audio_item.id
        assert rerecord_payload["rerecord_required"] is True
        assert rerecord_payload["retry"] is True
    finally:
        db.close()


def test_pending_audio_holds_level_promotion(monkeypatch):
    db = TestingSessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        audio_item, audio_step, _ = _content(db)
        session = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="in_progress",
            assigned_level=1,
        )
        db.add(session)
        db.flush()
        _pending_submission(db, student, session, audio_item, audio_step)
        db.commit()

        monkeypatch.setattr(
            navigation,
            "evaluate_student",
            lambda *_args, **_kwargs: {
                "ready": True,
                "decision_id": 999,
                "action": "promote",
                "previous_level": 1,
                "new_level": 2,
                "explanation": {"reason": "promotion_threshold_met"},
            },
        )
        monkeypatch.setattr(
            navigation,
            "prepare_next_for_student",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("promotion runtime must not execute while audio is unresolved")),
        )

        result = navigation._prepare_without_crossing_pending_audio(db, student, session)
        assert result["audio_review_pending"] is True
        assert result["level_transitioned"] is False
        assert result["decision"]["action"] == "hold"
        db.refresh(student)
        db.refresh(session)
        assert student.current_level == 1
        assert session.assigned_level == 1
        assert session.status == "in_progress"
    finally:
        db.close()
