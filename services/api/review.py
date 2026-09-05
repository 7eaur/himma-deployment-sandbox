from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from audio_review_policy import has_unresolved_audio, student_review_tasks
from dependencies import get_db, get_current_student, get_current_user
from db.models import (
    AssessmentSession,
    Attempt,
    AttemptResponse,
    AudioReview,
    AudioSubmission,
    AuditLog,
    ContentItem,
    ContentStep,
    Student,
    User,
)
import schemas

router = APIRouter(prefix="/review", tags=["Review"])


def _submission_context(db: Session, submission: AudioSubmission):
    response = db.query(AttemptResponse).filter(AttemptResponse.id == submission.response_id).first()
    attempt = db.query(Attempt).filter(Attempt.id == response.attempt_id).first() if response else None
    session = db.query(AssessmentSession).filter(AssessmentSession.id == attempt.session_id).first() if attempt else None
    student = db.query(Student).filter(Student.id == session.student_id).first() if session else None
    item = db.query(ContentItem).filter(ContentItem.id == attempt.item_id).first() if attempt else None
    step = db.query(ContentStep).filter(ContentStep.id == response.step_id).first() if response else None
    return response, attempt, session, student, item, step


@router.get("/pending-audio")
def get_pending_audio(
    db: Session = Depends(get_db),
    supervisor: User = Depends(get_current_user),
):
    """Return pending recordings with enough context for a meaningful review."""
    submissions = db.query(AudioSubmission).filter(
        AudioSubmission.status == "uploaded"
    ).order_by(AudioSubmission.submitted_at, AudioSubmission.id).all()

    payload: list[dict] = []
    for submission in submissions:
        response, attempt, session, student, item, step = _submission_context(db, submission)
        payload.append({
            "id": submission.id,
            "storage_key": submission.storage_key,
            "status": submission.status,
            "submitted_at": submission.submitted_at,
            "student_id": student.id if student else None,
            "student_name": student.name if student else "طالب غير معروف",
            "session_type": session.session_type if session else None,
            "item_title": (item.template_data or {}).get("title") if item else None,
            "expected_reading_text": step.expected_reading_text if step else None,
        })
    return payload


@router.get("/student-audio")
def get_student_audio_reviews(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    """Show unresolved recordings on the learner dashboard without blocking work."""
    return student_review_tasks(db, student_id=student.id)


@router.post("/student-audio/{submission_id}/begin-rerecord")
def begin_student_rerecord(
    submission_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    """Open exactly the reviewer-requested recording when the learner chooses it.

    The reviewer never reopens an old attempt automatically. Until this endpoint
    is called, the learner continues the current flow and the request remains a
    dashboard task.
    """
    submission = db.query(AudioSubmission).filter(AudioSubmission.id == submission_id).with_for_update().first()
    if not submission:
        raise HTTPException(status_code=404, detail="التسجيل غير موجود")
    response, attempt, session, owner, item, step = _submission_context(db, submission)
    if not response or not attempt or not session or not owner or owner.id != student.id:
        raise HTTPException(status_code=404, detail="طلب إعادة التسجيل غير موجود لهذا الطالب")
    if submission.status != "rerecord_required":
        raise HTTPException(status_code=409, detail="هذا التسجيل لا يحتاج إلى إعادة حاليًا")
    if session.status != "in_progress":
        raise HTTPException(status_code=409, detail="لا يمكن إعادة فتح تسجيل من مرحلة منتهية")

    attempt.status = "in_progress"
    attempt.completed_at = None
    db.add(AuditLog(
        actor_role="student",
        actor_id=student.id,
        action="student.audio.rerecord.begin",
        entity_type="AudioSubmission",
        entity_id=str(submission.id),
        details="Student explicitly opened reviewer-requested rerecord task from dashboard",
    ))
    db.commit()
    return {
        "status": "ok",
        "submission_id": submission.id,
        "session_id": session.id,
        "session_type": session.session_type,
        "item_id": attempt.item_id,
        "step_id": response.step_id,
    }


def _try_finalize_reviewed_assessment(db: Session, session: AssessmentSession | None) -> dict | None:
    if not session or session.session_type not in {"pretest", "posttest"} or session.status != "in_progress":
        return None
    attempts = db.query(Attempt).filter(Attempt.session_id == session.id).all()
    if len(attempts) != 30 or any(attempt.status != "completed" for attempt in attempts):
        return None
    if has_unresolved_audio(db, student_id=session.student_id, session_id=session.id):
        return None
    student = db.query(Student).filter(Student.id == session.student_id).first()
    if not student:
        return None
    from assessment_completion import finish_session
    return finish_session(db, student, session)


@router.post("/audio/{submission_id}/grade")
def grade_audio_submission(
    submission_id: int,
    request: schemas.GradeAudioRequest,
    db: Session = Depends(get_db),
    supervisor: User = Depends(get_current_user),
):
    """Grade audio without interrupting the learner's current activity flow."""
    submission = db.query(AudioSubmission).filter(AudioSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="التسجيل غير موجود")

    response, attempt, session, student, item, step = _submission_context(db, submission)
    if not response or not attempt:
        raise HTTPException(status_code=404, detail="إجابة الطالب المرتبطة بالتسجيل غير موجودة")

    if submission.status != "uploaded":
        raise HTTPException(status_code=409, detail="تمت معالجة هذا التسجيل مسبقًا")

    if not request.is_valid:
        # Important: do not reopen the old attempt here. The learner receives a
        # dashboard task and chooses when to enter the exact rerecord screen.
        submission.status = "rerecord_required"
        response.is_correct = None
        db.add(AuditLog(
            actor_role="researcher",
            actor_id=supervisor.id,
            action="request_audio_rerecord",
            entity_type="AudioSubmission",
            entity_id=str(submission.id),
            details="Recording marked invalid; rerecord queued for student dashboard without interrupting current flow",
        ))
        db.commit()
        return {"status": "ok", "message": "تم طلب إعادة التسجيل", "rerecord_queued": True}

    if not request.target_units or request.target_units <= 0:
        raise HTTPException(status_code=400, detail="أدخل عدد الوحدات أو الكلمات المستهدفة")

    if request.deletions + request.substitutions > request.target_units:
        raise HTTPException(
            status_code=400,
            detail="مجموع الحذف والاستبدال لا يمكن أن يتجاوز عدد الوحدات المستهدفة",
        )

    errors = request.deletions + request.substitutions + request.insertions
    rubric_score_val = max(0.0, 1.0 - (errors / request.target_units))
    rubric_score = Decimal(str(rubric_score_val))

    submission.status = "graded"
    response.is_correct = rubric_score > 0

    existing_review = db.query(AudioReview).filter(
        AudioReview.submission_id == submission.id
    ).order_by(AudioReview.id.desc()).first()

    review = AudioReview(
        submission_id=submission.id,
        reviewer_id=supervisor.id,
        target_units=request.target_units,
        deletions=request.deletions,
        substitutions=request.substitutions,
        insertions=request.insertions,
        rubric_score=rubric_score,
        supersedes_review_id=existing_review.id if existing_review else None,
        pronunciation_notes=request.pronunciation_notes,
        fluency_notes=request.fluency_notes,
        time_notes=request.time_notes,
    )
    db.add(review)
    db.add(AuditLog(
        actor_role="researcher",
        actor_id=supervisor.id,
        action="grade_audio",
        entity_type="AudioSubmission",
        entity_id=str(submission.id),
        details=f"Graded score={rubric_score}",
    ))

    db.flush()
    finalized = _try_finalize_reviewed_assessment(db, session)
    if finalized is None:
        db.commit()

    return {
        "status": "ok",
        "rubric_score": float(rubric_score),
        "assessment_finalized": finalized is not None,
        "final_score": float(finalized["final_score"]) if finalized else None,
        "assigned_level": finalized.get("assigned_level") if finalized else None,
    }
