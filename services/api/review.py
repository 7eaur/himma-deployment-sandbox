from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dependencies import get_db, get_current_user
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
        response = db.query(AttemptResponse).filter(
            AttemptResponse.id == submission.response_id
        ).first()
        attempt = db.query(Attempt).filter(Attempt.id == response.attempt_id).first() if response else None
        session = db.query(AssessmentSession).filter(
            AssessmentSession.id == attempt.session_id
        ).first() if attempt else None
        student = db.query(Student).filter(Student.id == session.student_id).first() if session else None
        item = db.query(ContentItem).filter(ContentItem.id == attempt.item_id).first() if attempt else None
        step = db.query(ContentStep).filter(ContentStep.id == response.step_id).first() if response else None
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


@router.post("/audio/{submission_id}/grade")
def grade_audio_submission(
    submission_id: int,
    request: schemas.GradeAudioRequest,
    db: Session = Depends(get_db),
    supervisor: User = Depends(get_current_user),
):
    """Grade an audio submission and preserve the manual review trail."""
    submission = db.query(AudioSubmission).filter(AudioSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="التسجيل غير موجود")

    response = db.query(AttemptResponse).filter(AttemptResponse.id == submission.response_id).first()
    if not response:
        raise HTTPException(status_code=404, detail="إجابة الطالب المرتبطة بالتسجيل غير موجودة")

    if submission.status != "uploaded":
        raise HTTPException(status_code=409, detail="تمت معالجة هذا التسجيل مسبقًا")

    if not request.is_valid:
        submission.status = "rerecord_required"
        response.is_correct = None
        attempt = db.query(Attempt).filter(Attempt.id == response.attempt_id).first()
        if not attempt:
            raise HTTPException(status_code=404, detail="محاولة الطالب غير موجودة")
        attempt.status = "in_progress"
        attempt.completed_at = None
        db.add(AuditLog(
            actor_role="researcher",
            actor_id=supervisor.id,
            action="request_audio_rerecord",
            entity_type="AudioSubmission",
            entity_id=str(submission.id),
            details="Recording marked invalid; student attempt reopened",
        ))
        db.commit()
        return {"status": "ok", "message": "تم طلب إعادة التسجيل"}

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

    db.commit()
    return {"status": "ok", "rubric_score": float(rubric_score)}
