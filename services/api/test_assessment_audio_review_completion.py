"""Regression coverage for pretest completion with real + skipped-style audio paths."""

import seed
import schemas
from content_runtime import canonical_interaction
from db.database import SessionLocal
from db.models import AssessmentSession, Attempt, AttemptResponse, AudioSubmission, ContentItem, Student, User
from protected import _assessment_display_status
from review import grade_audio_submission


AUDIO_INTERACTIONS = {"read_aloud", "timed_read_aloud"}


def test_completed_pretest_waits_for_real_audio_then_finalizes_placement():
    seed.run_seed()
    db = SessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    supervisor = db.query(User).filter(User.username == "researcher1").one()
    session = AssessmentSession(student_id=student.id, session_type="pretest", status="in_progress")
    db.add(session)
    db.flush()

    items = db.query(ContentItem).filter(ContentItem.kind == "pretest_question").order_by(ContentItem.order_index).all()
    assert len(items) == 30

    uploaded_submission = None
    for item in items:
        attempt = Attempt(session_id=session.id, item_id=item.id, status="completed")
        db.add(attempt)
        db.flush()
        step = item.steps[0]
        response = AttemptResponse(
            attempt_id=attempt.id,
            step_id=step.id,
            selected_option_id=None,
            is_correct=True,
            elapsed_seconds=0,
        )
        db.add(response)
        db.flush()

        # One real recording is enough to put a fully answered assessment into
        # review-wait. Other reading items emulate the neutral/handled path and
        # must not turn the assessment back into an answering state.
        if uploaded_submission is None and canonical_interaction(item) in AUDIO_INTERACTIONS:
            response.is_correct = None
            uploaded_submission = AudioSubmission(
                response_id=response.id,
                storage_key="tests/pretest-reading.webm",
                file_size=1234,
                mime_type="audio/webm",
                duration_seconds=2,
                status="uploaded",
            )
            db.add(uploaded_submission)

    db.commit()
    db.refresh(session)
    db.refresh(student)
    assert uploaded_submission is not None
    submission_id = uploaded_submission.id
    session_id = session.id
    original_level = student.current_level

    assert _assessment_display_status(db, session) == "waiting_audio_review"
    assert session.status == "in_progress"
    assert student.current_level == original_level

    result = grade_audio_submission(
        submission_id,
        schemas.GradeAudioRequest(
            is_valid=True,
            target_units=1,
            deletions=0,
            substitutions=0,
            insertions=0,
        ),
        db=db,
        supervisor=supervisor,
    )

    assert result["assessment_finalized"] is True
    assert result["assigned_level"] in {1, 2, 3}

    db.expire_all()
    finalized_session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).one()
    refreshed_student = db.query(Student).filter(Student.id == student.id).one()
    assert finalized_session.status == "completed"
    assert finalized_session.assigned_level == result["assigned_level"]
    assert refreshed_student.current_level == result["assigned_level"]
    assert finalized_session.final_score is not None
    db.close()
