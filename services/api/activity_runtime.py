"""Canonical adaptive-learning HTTP runtime.

This module owns the mounted ``/activities`` routes.  It reuses the proven
Stage-2 scoring/adaptation services, but makes the learner reading-review state
explicit so a persisted recording can never become completion evidence before
supervisor review.

Important invariants:
- required student audio has no skip/bypass path;
- an uploaded recording is pending evidence, not a correct answer;
- supervisor review is authoritative: ``graded`` may satisfy the step and
  ``rerecord_required`` reopens it;
- historical Stage-2 helpers stay available as service code, while this module
  is the single public route owner.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import storage
from activities import (
    ActivitySubmitRequest,
    _activity_session_or_404,
    _finalize_session_if_done,
    _load_item,
    _pending_attempt,
    _progress_payload,
    _rich_item_query,
    _step_payload as stage2_step_payload,
    _step_state as stage2_step_state,
    learning_status as stage2_learning_status,
    start_learning as stage2_start_learning,
    submit_activity_step as stage2_submit_activity_step,
)
from activities_v4 import _next_unused_core_item, _resolve_active_session
from adaptation_runtime import prepare_next_for_student
from assessment import (
    _commit_idempotent,
    _idempotency_replay,
    _request_hash,
    _store_idempotency,
    _validate_idempotency_key,
)
from content_runtime import canonical_interaction
from db.models import (
    AssessmentSession,
    Attempt,
    AttemptResponse,
    AudioSubmission,
    ContentItem,
    ContentStep,
    Student,
)
from dependencies import get_current_student, get_db

router = APIRouter(tags=["Activities"])
AUDIO_INTERACTIONS = {"read_aloud", "timed_read_aloud"}
PENDING_AUDIO_STATUSES = {"uploaded", "pending"}


class ActivityRuntimeSubmitRequest(BaseModel):
    step_id: int
    selected_option_ids: list[int] = Field(default_factory=list, max_length=20)
    hint_used: bool = False
    elapsed_seconds: int = Field(default=0, ge=0, le=3600)
    # Compatibility input only. Novel skip evidence is rejected below.
    declared_media_gap_skip: bool = False
    audio_storage_key: Optional[str] = None
    audio_file_size: Optional[int] = Field(default=None, gt=0)
    audio_mime_type: Optional[str] = None
    audio_duration_seconds: Optional[Decimal] = Field(default=None, ge=0)


def _audio_for_response(db: Session, response: AttemptResponse | None) -> AudioSubmission | None:
    if response is None:
        return None
    return (
        db.query(AudioSubmission)
        .filter(AudioSubmission.response_id == response.id)
        .order_by(AudioSubmission.id.desc())
        .first()
    )


def effective_step_state(db: Session, attempt: Attempt, step: ContentStep) -> dict[str, Any]:
    """Return fail-closed step state for supervisor-reviewed reading evidence."""
    response = (
        db.query(AttemptResponse)
        .filter(
            AttemptResponse.attempt_id == attempt.id,
            AttemptResponse.step_id == step.id,
        )
        .order_by(AttemptResponse.id.desc())
        .first()
    )
    audio = _audio_for_response(db, response)
    if audio is None:
        return stage2_step_state(db, attempt, step)

    base = {
        "attempts_used": 1,
        "reinforcement_verification": False,
        "reinforcement_cycle_id": None,
        "audio_review_status": audio.status,
    }
    if audio.status in PENDING_AUDIO_STATUSES:
        return {
            **base,
            "done": False,
            "last_correct": None,
            "awaiting_audio_review": True,
        }
    if audio.status == "rerecord_required":
        return {
            **base,
            "done": False,
            "last_correct": None,
            "awaiting_audio_review": False,
        }
    if audio.status == "graded":
        return {
            **base,
            "done": True,
            "last_correct": response.is_correct,
            "awaiting_audio_review": False,
        }

    # Unknown review states fail closed. They must never count as completion.
    return {
        **base,
        "done": False,
        "last_correct": None,
        "awaiting_audio_review": True,
    }


def _runtime_step_payload(
    db: Session,
    item: ContentItem,
    attempt: Attempt,
    step: ContentStep,
) -> dict[str, Any]:
    payload = stage2_step_payload(db, item, attempt, step)
    state = effective_step_state(db, attempt, step)
    payload["attempts_used"] = state["attempts_used"]
    payload["retry"] = state["attempts_used"] > 0 and not state["done"] and not state.get("awaiting_audio_review")
    payload["hint_available"] = payload["retry"]
    payload["audio_review_status"] = state.get("audio_review_status")
    payload["awaiting_audio_review"] = bool(state.get("awaiting_audio_review"))
    return payload


def _finalize_attempt_if_done(db: Session, attempt: Attempt, item: ContentItem) -> None:
    for step in item.steps:
        if not effective_step_state(db, attempt, step)["done"]:
            return
    attempt.status = "completed"
    attempt.completed_at = datetime.now(timezone.utc)


def _validate_learning_audio(
    *,
    student: Student,
    body: ActivityRuntimeSubmitRequest,
) -> None:
    if body.selected_option_ids:
        raise HTTPException(status_code=400, detail="جولة القراءة الجهرية تستقبل تسجيلًا صوتيًا فقط")
    if not body.audio_storage_key:
        raise HTTPException(status_code=400, detail="التسجيل الصوتي مطلوب قبل إرسال الجولة")
    if not body.audio_storage_key.startswith(f"audio/{student.id}/"):
        raise HTTPException(status_code=400, detail="مسار التسجيل الصوتي غير صالح")
    if body.audio_file_size is None or body.audio_file_size <= 0:
        raise HTTPException(status_code=400, detail="حجم التسجيل الصوتي غير صالح")
    if not body.audio_mime_type or not body.audio_mime_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="نوع التسجيل الصوتي غير صالح")
    try:
        storage.verify_audio(
            body.audio_storage_key,
            expected_size=body.audio_file_size,
            expected_content_type=body.audio_mime_type,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail="تعذر التحقق من التسجيل الصوتي المحفوظ") from exc


def _submit_learning_audio(
    *,
    session: AssessmentSession,
    item_id: int,
    body: ActivityRuntimeSubmitRequest,
    idempotency_key: str,
    db: Session,
    student: Student,
) -> dict[str, Any]:
    _validate_idempotency_key(idempotency_key)
    payload_hash = _request_hash(body.model_dump(mode="json"))
    operation = f"activity_audio_submit:{session.id}:{item_id}:{body.step_id}"
    replay = _idempotency_replay(db, student.id, operation, idempotency_key, payload_hash)
    if replay is not None:
        return replay

    attempt = db.query(Attempt).filter(
        Attempt.session_id == session.id,
        Attempt.item_id == item_id,
        Attempt.status == "in_progress",
    ).first()
    if attempt is None:
        raise HTTPException(status_code=404, detail="محاولة النشاط غير موجودة أو انتهت")

    item = _load_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="النشاط غير موجود")
    if canonical_interaction(item) not in AUDIO_INTERACTIONS:
        raise HTTPException(status_code=400, detail="هذه الجولة لا تستقبل تسجيلًا صوتيًا")

    step = next((candidate for candidate in item.steps if candidate.id == body.step_id), None)
    if step is None:
        raise HTTPException(status_code=400, detail="الجولة لا تنتمي إلى هذا النشاط")

    _validate_learning_audio(student=student, body=body)

    response = db.query(AttemptResponse).filter(
        AttemptResponse.attempt_id == attempt.id,
        AttemptResponse.step_id == step.id,
    ).order_by(AttemptResponse.id.desc()).first()
    audio = _audio_for_response(db, response)

    if response is not None:
        if audio is None:
            raise HTTPException(status_code=409, detail="حالة التسجيل الحالية غير مكتملة. تواصل مع المشرف")
        if audio.status in PENDING_AUDIO_STATUSES:
            raise HTTPException(status_code=409, detail="التسجيل محفوظ وينتظر مراجعة المشرف")
        if audio.status == "graded":
            raise HTTPException(status_code=409, detail="تمت مراجعة هذا التسجيل مسبقًا")
        if audio.status != "rerecord_required":
            raise HTTPException(status_code=409, detail="حالة التسجيل الحالية لا تسمح بإعادة الإرسال")

        response.is_correct = None
        response.elapsed_seconds = body.elapsed_seconds
        audio.storage_key = body.audio_storage_key
        audio.file_size = body.audio_file_size
        audio.mime_type = body.audio_mime_type
        audio.duration_seconds = body.audio_duration_seconds
        audio.status = "uploaded"
        audio.submitted_at = datetime.now(timezone.utc)
    else:
        response = AttemptResponse(
            attempt_id=attempt.id,
            step_id=step.id,
            selected_option_id=None,
            is_correct=None,
            elapsed_seconds=body.elapsed_seconds,
        )
        db.add(response)
        db.flush()
        audio = AudioSubmission(
            response_id=response.id,
            storage_key=body.audio_storage_key,
            file_size=body.audio_file_size,
            mime_type=body.audio_mime_type,
            duration_seconds=body.audio_duration_seconds,
            status="uploaded",
        )
        db.add(audio)

    attempt.elapsed_seconds = int(attempt.elapsed_seconds or 0) + body.elapsed_seconds
    session.elapsed_seconds = int(session.elapsed_seconds or 0) + body.elapsed_seconds
    session.updated_at = datetime.now(timezone.utc)

    result: dict[str, Any] = {
        "status": "ok",
        "is_correct": None,
        "step_complete": False,
        "activity_complete": False,
        "learning_complete": False,
        "awaiting_review": True,
        "audio_review_status": "uploaded",
    }
    _store_idempotency(db, student.id, operation, idempotency_key, payload_hash, result)
    return _commit_idempotent(db, student.id, operation, idempotency_key, payload_hash, result)


@router.get("/activities/status")
def learning_status(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return stage2_learning_status(db=db, student=student)


@router.post("/activities/start")
def start_learning(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return stage2_start_learning(db=db, student=student)


@router.get("/activities/session/{session_id}/progress")
def learning_progress(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = _resolve_active_session(
        db,
        requested_session_id=session_id,
        student_id=student.id,
    )
    return _progress_payload(db, session, session.assigned_level or student.current_level)


@router.get("/activities/session/{session_id}/next")
def next_activity_step(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = _resolve_active_session(
        db,
        requested_session_id=session_id,
        student_id=student.id,
    )

    pending_attempt = _pending_attempt(db, session.id)
    if pending_attempt:
        item = _load_item(db, pending_attempt.item_id)
        if not item:
            raise HTTPException(status_code=409, detail="تعذر تحميل محتوى النشاط")
        for step in item.steps:
            if not effective_step_state(db, pending_attempt, step)["done"]:
                return _runtime_step_payload(db, item, pending_attempt, step)
        _finalize_attempt_if_done(db, pending_attempt, item)
        db.commit()

    prepared = prepare_next_for_student(db, student, session)
    if prepared.get("mapping_blocked"):
        raise HTTPException(
            status_code=409,
            detail="يحتاج المسار إلى ربط نشاط تقوية معتمد للمهارة الأضعف قبل المتابعة.",
        )
    if prepared.get("verification_escalated"):
        raise HTTPException(
            status_code=409,
            detail="يحتاج هذا الضعف إلى مراجعة المشرف بعد محاولات التقوية والتحقق.",
        )
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
            (step for step in item.steps if not effective_step_state(db, pending_attempt, step)["done"]),
            None,
        )
        if first_pending:
            return _runtime_step_payload(db, item, pending_attempt, first_pending)
        _finalize_attempt_if_done(db, pending_attempt, item)
        db.commit()

    item = _next_unused_core_item(
        db,
        student_id=student.id,
        session_id=session.id,
        level_id=level_id,
    )
    if not item:
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
        attempt = db.query(Attempt).filter(
            Attempt.session_id == session.id,
            Attempt.item_id == item.id,
        ).one()

    first_step = next(iter(item.steps), None)
    if not first_step:
        raise HTTPException(status_code=409, detail="النشاط لا يحتوي على جولات معتمدة")
    return _runtime_step_payload(db, item, attempt, first_step)


@router.post("/activities/session/{session_id}/attempt/{item_id}/submit")
def submit_activity_step(
    session_id: int,
    item_id: int,
    body: ActivityRuntimeSubmitRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = _resolve_active_session(
        db,
        requested_session_id=session_id,
        student_id=student.id,
    )

    # Historical skip fields remain readable in old records, but no current
    # public request can manufacture completion from a missing media asset.
    if body.declared_media_gap_skip:
        raise HTTPException(
            status_code=409,
            detail="لا يمكن تجاوز أصل تعليمي مطلوب أو احتساب الجولة دون دليل فعلي",
        )

    item = _load_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="النشاط غير موجود")
    interaction = canonical_interaction(item)

    if interaction in AUDIO_INTERACTIONS:
        return _submit_learning_audio(
            session=session,
            item_id=item_id,
            body=body,
            idempotency_key=idempotency_key,
            db=db,
            student=student,
        )

    if any([
        body.audio_storage_key,
        body.audio_file_size,
        body.audio_mime_type,
        body.audio_duration_seconds is not None,
    ]):
        raise HTTPException(status_code=400, detail="هذه الجولة لا تستقبل تسجيلًا صوتيًا")

    stage2_body = ActivitySubmitRequest(
        step_id=body.step_id,
        selected_option_ids=body.selected_option_ids,
        hint_used=body.hint_used,
        elapsed_seconds=body.elapsed_seconds,
        declared_media_gap_skip=False,
    )
    return stage2_submit_activity_step(
        session_id=session.id,
        item_id=item_id,
        body=stage2_body,
        idempotency_key=idempotency_key,
        db=db,
        student=student,
    )
