from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db.models import AssessmentSession, Attempt, AttemptResponse, AudioSubmission, Student, User
from db.notification_models import ResearcherNotification
from db.reinforcement_models import ReinforcementCycle
from dependencies import get_current_user, get_db

router = APIRouter(prefix="/researcher/notifications", tags=["Researcher Notifications"])


def _upsert_notification(
    db: Session,
    *,
    dedupe_key: str,
    notification_type: str,
    title: str,
    message: str,
    href: str,
    entity_type: str,
    entity_id: str,
) -> None:
    existing = db.query(ResearcherNotification).filter(
        ResearcherNotification.dedupe_key == dedupe_key,
    ).first()
    if existing:
        return
    db.add(ResearcherNotification(
        dedupe_key=dedupe_key,
        notification_type=notification_type,
        title=title,
        message=message,
        href=href,
        entity_type=entity_type,
        entity_id=entity_id,
        is_read=False,
        created_at=datetime.now(timezone.utc),
    ))


def _sync_actionable_notifications(db: Session) -> None:
    """Materialize current action-required domain states into a durable inbox.

    Domain tables remain authoritative. The notification table only stores the
    supervisor attention/read model and never drives academic decisions.
    """
    pending_audio = (
        db.query(AudioSubmission, AssessmentSession, Student)
        .join(AttemptResponse, AttemptResponse.id == AudioSubmission.response_id)
        .join(Attempt, Attempt.id == AttemptResponse.attempt_id)
        .join(AssessmentSession, AssessmentSession.id == Attempt.session_id)
        .join(Student, Student.id == AssessmentSession.student_id)
        .filter(AudioSubmission.status == "uploaded")
        .all()
    )
    active_audio_keys: set[str] = set()
    for submission, session, student in pending_audio:
        key = f"audio-review:{submission.id}"
        active_audio_keys.add(key)
        _upsert_notification(
            db,
            dedupe_key=key,
            notification_type="audio_review_required",
            title="تسجيل جديد يحتاج مراجعة",
            message=f"لدى {student.name} تسجيل قراءة بانتظار المراجعة.",
            href="/admin/audio-review",
            entity_type="audio_submission",
            entity_id=str(submission.id),
        )

    stale_audio = db.query(ResearcherNotification).filter(
        ResearcherNotification.notification_type == "audio_review_required",
        ResearcherNotification.is_read.is_(False),
    ).all()
    now = datetime.now(timezone.utc)
    for notification in stale_audio:
        if notification.dedupe_key not in active_audio_keys:
            notification.is_read = True
            notification.read_at = notification.read_at or now

    escalated_cycles = (
        db.query(ReinforcementCycle, Student)
        .join(Student, Student.id == ReinforcementCycle.student_id)
        .filter(ReinforcementCycle.status == "escalated")
        .all()
    )
    for cycle, student in escalated_cycles:
        _upsert_notification(
            db,
            dedupe_key=f"reinforcement-escalated:{cycle.id}",
            notification_type="reinforcement_attention",
            title="طالب يحتاج متابعة",
            message=f"وصلت تقوية {student.name} إلى حالة تحتاج تدخل المشرف.",
            href=f"/admin/students/{student.id}",
            entity_type="reinforcement_cycle",
            entity_id=str(cycle.id),
        )

    db.commit()


def _payload(notification: ResearcherNotification) -> dict:
    return {
        "id": notification.id,
        "type": notification.notification_type,
        "title": notification.title,
        "message": notification.message,
        "href": notification.href,
        "entity_type": notification.entity_type,
        "entity_id": notification.entity_id,
        "is_read": bool(notification.is_read),
        "created_at": notification.created_at,
        "read_at": notification.read_at,
    }


@router.get("")
def list_notifications(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _sync_actionable_notifications(db)
    rows = (
        db.query(ResearcherNotification)
        .order_by(ResearcherNotification.is_read.asc(), ResearcherNotification.created_at.desc(), ResearcherNotification.id.desc())
        .limit(limit)
        .all()
    )
    unread = db.query(ResearcherNotification.id).filter(ResearcherNotification.is_read.is_(False)).count()
    return {"unread_count": unread, "items": [_payload(row) for row in rows]}


@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = db.query(ResearcherNotification).filter(ResearcherNotification.id == notification_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="الإشعار غير موجود")
    if not row.is_read:
        row.is_read = True
        row.read_at = datetime.now(timezone.utc)
        db.commit()
    return _payload(row)


@router.post("/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    rows = db.query(ResearcherNotification).filter(ResearcherNotification.is_read.is_(False)).all()
    for row in rows:
        row.is_read = True
        row.read_at = now
    db.commit()
    return {"updated": len(rows)}
