"""Regression coverage for the student assessment display state.

The assessment session stays academically ``in_progress`` while the profile
exposes whether the learner is still answering, waiting for manual audio
review, needs a rerecord, or is ready to finalize.
"""

from db.database import SessionLocal
from db.models import AssessmentSession, Attempt, AttemptResponse, AudioSubmission, ContentItem, Student
from protected import _assessment_display_status
import seed


def test_assessment_display_status_exposes_audio_wait_before_all_questions_are_done():
    seed.run_seed()
    db = SessionLocal()
    try:
        audio_item = (
            db.query(ContentItem)
            .filter(
                ContentItem.kind == "pretest_question",
                ContentItem.interaction_type == "read_aloud",
            )
            .order_by(ContentItem.order_index, ContentItem.id)
            .first()
        )
        assert audio_item is not None

        student = Student(
            access_code="947250",
            name="طالب انتظار مبكر",
            grade_level=3,
            current_level=1,
            is_active=True,
        )
        db.add(student)
        db.flush()

        session = AssessmentSession(student_id=student.id, session_type="pretest", status="in_progress")
        db.add(session)
        db.flush()

        attempt = Attempt(session_id=session.id, item_id=audio_item.id, status="completed")
        db.add(attempt)
        db.flush()
        response = AttemptResponse(attempt_id=attempt.id, step_id=audio_item.steps[0].id)
        db.add(response)
        db.flush()
        submission = AudioSubmission(
            response_id=response.id,
            storage_key="tests/mid-assessment-pending.webm",
            file_size=2048,
            mime_type="audio/webm",
            status="uploaded",
        )
        db.add(submission)
        db.flush()

        assert _assessment_display_status(db, session) == "waiting_audio_review"
        assert session.status == "in_progress"

        submission.status = "rerecord_required"
        db.flush()
        assert _assessment_display_status(db, session) == "rerecord_required"
        assert session.status == "in_progress"
    finally:
        db.close()


def test_assessment_display_status_tracks_audio_review_without_mutating_session():
    seed.run_seed()
    db = SessionLocal()
    try:
        items = (
            db.query(ContentItem)
            .filter(ContentItem.kind == "pretest_question")
            .order_by(ContentItem.order_index, ContentItem.id)
            .all()
        )
        assert len(items) == 30

        student = Student(
            access_code="947251",
            name="طالب مراجعة صوتية",
            grade_level=3,
            current_level=1,
            is_active=True,
        )
        db.add(student)
        db.flush()

        session = AssessmentSession(student_id=student.id, session_type="pretest", status="in_progress")
        db.add(session)
        db.flush()

        for item in items[:29]:
            db.add(Attempt(session_id=session.id, item_id=item.id, status="completed"))
        db.flush()
        assert _assessment_display_status(db, session) == "answering"
        assert session.status == "in_progress"

        final_attempt = Attempt(session_id=session.id, item_id=items[29].id, status="completed")
        db.add(final_attempt)
        db.flush()
        assert _assessment_display_status(db, session) == "ready_to_finalize"
        assert session.status == "in_progress"

        step = items[29].steps[0]
        response = AttemptResponse(attempt_id=final_attempt.id, step_id=step.id)
        db.add(response)
        db.flush()
        submission = AudioSubmission(
            response_id=response.id,
            storage_key="tests/pending-reading.webm",
            file_size=2048,
            mime_type="audio/webm",
            status="uploaded",
        )
        db.add(submission)
        db.flush()
        assert _assessment_display_status(db, session) == "waiting_audio_review"
        assert session.status == "in_progress"

        submission.status = "rerecord_required"
        db.flush()
        assert _assessment_display_status(db, session) == "rerecord_required"
        assert session.status == "in_progress"
    finally:
        db.close()
