"""Shared audio-review state helpers for the student learning journey.

Pending review is asynchronous: it may hold a phase/level boundary, but it must
not interrupt the learner's remaining work inside the current phase. A
``rerecord_required`` submission stays as a dashboard task until the student
explicitly opens it for rerecording.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from db.models import (
    AssessmentSession,
    Attempt,
    AttemptResponse,
    AudioSubmission,
    ContentItem,
    ContentStep,
)

PENDING_REVIEW_STATUSES = {"uploaded", "pending"}
UNRESOLVED_REVIEW_STATUSES = {"uploaded", "pending", "rerecord_required"}


def unresolved_audio_query(db: Session, *, student_id: int, session_id: int | None = None):
    query = (
        db.query(AudioSubmission)
        .join(AttemptResponse, AttemptResponse.id == AudioSubmission.response_id)
        .join(Attempt, Attempt.id == AttemptResponse.attempt_id)
        .join(AssessmentSession, AssessmentSession.id == Attempt.session_id)
        .filter(
            AssessmentSession.student_id == student_id,
            AudioSubmission.status.in_(UNRESOLVED_REVIEW_STATUSES),
        )
    )
    if session_id is not None:
        query = query.filter(AssessmentSession.id == session_id)
    return query


def has_unresolved_audio(db: Session, *, student_id: int, session_id: int | None = None) -> bool:
    return unresolved_audio_query(db, student_id=student_id, session_id=session_id).first() is not None


def review_summary(db: Session, *, student_id: int, session_id: int | None = None) -> dict[str, int | bool]:
    rows = unresolved_audio_query(db, student_id=student_id, session_id=session_id).all()
    waiting = sum(1 for row in rows if row.status in PENDING_REVIEW_STATUSES)
    rerecord = sum(1 for row in rows if row.status == "rerecord_required")
    return {
        "pending_count": waiting,
        "rerecord_required_count": rerecord,
        "unresolved_count": len(rows),
        "audio_review_pending": bool(rows),
    }


def student_review_tasks(db: Session, *, student_id: int) -> list[dict[str, Any]]:
    submissions = (
        unresolved_audio_query(db, student_id=student_id)
        .order_by(AudioSubmission.submitted_at, AudioSubmission.id)
        .all()
    )
    payload: list[dict[str, Any]] = []
    for submission in submissions:
        response = db.query(AttemptResponse).filter(AttemptResponse.id == submission.response_id).first()
        attempt = db.query(Attempt).filter(Attempt.id == response.attempt_id).first() if response else None
        session = db.query(AssessmentSession).filter(AssessmentSession.id == attempt.session_id).first() if attempt else None
        item = db.query(ContentItem).filter(ContentItem.id == attempt.item_id).first() if attempt else None
        step = db.query(ContentStep).filter(ContentStep.id == response.step_id).first() if response else None
        if not response or not attempt or not session:
            continue
        payload.append({
            "id": submission.id,
            "status": submission.status,
            "submitted_at": submission.submitted_at,
            "session_id": session.id,
            "session_type": session.session_type,
            "level_id": session.assigned_level,
            "item_id": attempt.item_id,
            "step_id": response.step_id,
            "item_title": (item.template_data or {}).get("title") if item else None,
            "expected_reading_text": step.expected_reading_text if step else None,
            "can_rerecord": submission.status == "rerecord_required",
        })
    return payload
