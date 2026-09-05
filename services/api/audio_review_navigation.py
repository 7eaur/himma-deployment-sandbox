"""Student learning navigation with asynchronous audio review.

A submitted reading recording counts as *navigated* so the learner can continue
remaining activities, while it stays academically unresolved until supervisor
review. Unresolved audio therefore blocks only level promotion/completion.
A rerecord request interrupts the flow only after the learner explicitly opens
that task from the dashboard (the review route reopens that exact attempt).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from activities import (
    _activity_session_or_404,
    _finalize_session_if_done,
    _load_item,
    _pending_attempt,
    _progress_payload,
    _step_payload as stage2_step_payload,
    _step_state as stage2_step_state,
    learning_status as stage2_learning_status,
)
from activities_v4 import _next_unused_core_item, _resolve_active_session
from adaptation import evaluate_student
from adaptation_runtime import prepare_next_for_student
from audio_review_policy import PENDING_REVIEW_STATUSES, has_unresolved_audio, review_summary
from db.models import Attempt, AttemptResponse, AudioSubmission, AuditLog, ContentItem, ContentStep, Student
from dependencies import get_current_student, get_db

router = APIRouter(tags=["Activities asynchronous audio review"])


def _latest_audio(db: Session, attempt: Attempt, step: ContentStep) -> tuple[AttemptResponse | None, AudioSubmission | None]:
    response = (
        db.query(AttemptResponse)
        .filter(AttemptResponse.attempt_id == attempt.id, AttemptResponse.step_id == step.id)
        .order_by(AttemptResponse.id.desc())
        .first()
    )
    if response is None:
        return None, None
    audio = (
        db.query(AudioSubmission)
        .filter(AudioSubmission.response_id == response.id)
        .order_by(AudioSubmission.id.desc())
        .first()
    )
    return response, audio


def _rerecord_explicitly_opened(db: Session, submission_id: int) -> bool:
    return db.query(AuditLog.id).filter(
        AuditLog.actor_role == "student",
        AuditLog.action == "student.audio.rerecord.begin",
        AuditLog.entity_type == "AudioSubmission",
        AuditLog.entity_id == str(submission_id),
    ).first() is not None


def _navigation_step_state(db: Session, attempt: Attempt, step: ContentStep) -> dict[str, Any]:
    response, audio = _latest_audio(db, attempt, step)
    if audio is None:
        return stage2_step_state(db, attempt, step)

    base = {
        "attempts_used": 1,
        "reinforcement_verification": False,
        "reinforcement_cycle_id": None,
        "audio_review_status": audio.status,
        "awaiting_audio_review": False,
        "rerecord_required": False,
        "rerecord_opened": False,
    }
    if audio.status in PENDING_REVIEW_STATUSES:
        # The learner has done their part. Keep the evidence neutral, but do not
        # make them sit on this screen while the supervisor reviews it.
        return {**base, "done": True, "last_correct": None, "awaiting_audio_review": True}
    if audio.status == "rerecord_required":
        opened = _rerecord_explicitly_opened(db, audio.id)
        return {
            **base,
            "done": not opened,
            "last_correct": None,
            "rerecord_required": True,
            "rerecord_opened": opened,
        }
    if audio.status == "graded":
        return {**base, "done": True, "last_correct": response.is_correct if response else None}
    return {**base, "done": False, "last_correct": None, "awaiting_audio_review": True}


def _navigation_step_payload(db: Session, item: ContentItem, attempt: Attempt, step: ContentStep) -> dict[str, Any]:
    payload = stage2_step_payload(db, item, attempt, step)
    state = _navigation_step_state(db, attempt, step)
    payload["attempts_used"] = state["attempts_used"]
    payload["retry"] = bool(state.get("rerecord_required") and state.get("rerecord_opened"))
    payload["hint_available"] = payload["retry"]
    payload["audio_review_status"] = state.get("audio_review_status")
    payload["awaiting_audio_review"] = bool(state.get("awaiting_audio_review"))
    payload["rerecord_required"] = bool(state.get("rerecord_required"))
    return payload


def _finish_navigation_attempt(db: Session, attempt: Attempt, item: ContentItem) -> None:
    for step in item.steps:
        if not _navigation_step_state(db, attempt, step)["done"]:
            return
    attempt.status = "completed"
    attempt.completed_at = datetime.now(timezone.utc)


def _prepare_without_crossing_pending_audio(db: Session, student: Student, session) -> dict:
    if not has_unresolved_audio(db, student_id=student.id, session_id=session.id):
        return prepare_next_for_student(db, student, session)

    preview = evaluate_student(db, student, session_id=session.id)
    explanation = dict(preview.get("explanation") or {})
    would_promote = preview.get("ready") and preview.get("action") == "promote"
    would_complete_l3 = (
        preview.get("ready")
        and int(preview.get("previous_level") or session.assigned_level or student.current_level) == 3
        and explanation.get("reason") == "top_level_mastery"
    )
    if would_promote or would_complete_l3:
        return {
            "continue_learning": True,
            "decision": {
                **preview,
                "action": "hold",
                "new_level": session.assigned_level,
                "reason": "audio_review_pending_before_level_transition",
                "explanation": {
                    **explanation,
                    "audio_review_pending": True,
                    "reason": "audio_review_pending_before_level_transition",
                },
            },
            "recommended_attempt_id": None,
            "verification_attempt_id": None,
            "mapping_blocked": False,
            "recommendation_fulfilled": False,
            "verification_escalated": False,
            "level_id": session.assigned_level,
            "session_id": session.id,
            "level_transitioned": False,
            "audio_review_pending": True,
        }
    # Same-level support/reinforcement must continue normally; only crossing the
    # level boundary is held by unresolved audio.
    return prepare_next_for_student(db, student, session)


@router.get("/activities/status")
def learning_status(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    payload = stage2_learning_status(db=db, student=student)
    session_id = payload.get("session_id")
    if session_id:
        payload.update(review_summary(db, student_id=student.id, session_id=int(session_id)))
    else:
        payload.update({
            "pending_count": 0,
            "rerecord_required_count": 0,
            "unresolved_count": 0,
            "audio_review_pending": False,
        })
    return payload


@router.get("/activities/session/{session_id}/progress")
def learning_progress(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = _resolve_active_session(db, requested_session_id=session_id, student_id=student.id)
    payload = _progress_payload(db, session, session.assigned_level or student.current_level)
    payload.update(review_summary(db, student_id=student.id, session_id=session.id))
    return payload


@router.get("/activities/session/{session_id}/next")
def next_activity_step(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = _resolve_active_session(db, requested_session_id=session_id, student_id=student.id)

    pending_attempt = _pending_attempt(db, session.id)
    if pending_attempt:
        item = _load_item(db, pending_attempt.item_id)
        if not item:
            raise HTTPException(status_code=409, detail="تعذر تحميل محتوى النشاط")
        first_pending = next(
            (step for step in item.steps if not _navigation_step_state(db, pending_attempt, step)["done"]),
            None,
        )
        if first_pending:
            return _navigation_step_payload(db, item, pending_attempt, first_pending)
        _finish_navigation_attempt(db, pending_attempt, item)
        db.commit()

    prepared = _prepare_without_crossing_pending_audio(db, student, session)
    if prepared.get("mapping_blocked"):
        raise HTTPException(status_code=409, detail="يحتاج المسار إلى ربط نشاط تقوية معتمد للمهارة الأضعف قبل المتابعة.")
    if prepared.get("verification_escalated"):
        raise HTTPException(status_code=409, detail="يحتاج هذا الضعف إلى مراجعة المشرف بعد محاولات التقوية والتحقق.")
    if prepared.get("journey_completed"):
        return None

    prepared_session_id = int(prepared.get("session_id") or session.id)
    if prepared_session_id != session.id:
        session = _activity_session_or_404(db, prepared_session_id, student.id)

    db.refresh(session)
    db.refresh(student)
    level_id = session.assigned_level or student.current_level

    pending_attempt = _pending_attempt(db, session.id)
    if pending_attempt:
        item = _load_item(db, pending_attempt.item_id)
        if not item:
            raise HTTPException(status_code=409, detail="تعذر تحميل نشاط التقوية أو التحقق")
        first_pending = next(
            (step for step in item.steps if not _navigation_step_state(db, pending_attempt, step)["done"]),
            None,
        )
        if first_pending:
            return _navigation_step_payload(db, item, pending_attempt, first_pending)
        _finish_navigation_attempt(db, pending_attempt, item)
        db.commit()

    item = _next_unused_core_item(
        db,
        student_id=student.id,
        session_id=session.id,
        level_id=level_id,
    )
    if not item:
        if has_unresolved_audio(db, student_id=student.id, session_id=session.id):
            # All available work is done, but the level remains active until the
            # review/rerecord boundary is resolved. The dashboard communicates
            # the pending state and provides the rerecord entry point.
            return None
        _finalize_session_if_done(db, session, level_id)
        db.commit()
        if session.status == "completed":
            return None
        raise HTTPException(status_code=409, detail="لا يمكن متابعة المسار دون محتوى معتمد مطابق")

    attempt = Attempt(session_id=session.id, item_id=item.id, status="in_progress")
    db.add(attempt)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        attempt = db.query(Attempt).filter(Attempt.session_id == session.id, Attempt.item_id == item.id).one()

    first_step = next(iter(item.steps), None)
    if not first_step:
        raise HTTPException(status_code=409, detail="النشاط لا يحتوي على جولات معتمدة")
    return _navigation_step_payload(db, item, attempt, first_step)
