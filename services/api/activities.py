"""Adaptive learning activity runtime.

The accepted Stage-2 core runner remains the durable execution base. This
recovery layer restores the canonical interaction/media contract so each
approved learning activity is rendered as designed instead of collapsing into
a generic text-choice screen.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from assessment import (
    _commit_idempotent,
    _idempotency_replay,
    _request_hash,
    _store_idempotency,
    _validate_idempotency_key,
)
from content_runtime import (
    canonical_id,
    canonical_interaction,
    instruction_text,
    item_assets,
    media_gaps,
    step_assets,
)
from db.activity_models import ActivityStepResponse
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
from reinforcement_cycles import (
    active_verification_cycle,
    finish_verification_step,
    verification_response_count,
)

router = APIRouter(prefix="/activities", tags=["Activities"])

MAX_STEP_ATTEMPTS = 2
CORE_ACTIVITY_COUNT = 10


class ActivitySubmitRequest(BaseModel):
    step_id: int
    selected_option_ids: list[int] = Field(default_factory=list, max_length=20)
    hint_used: bool = False
    elapsed_seconds: int = Field(default=0, ge=0, le=3600)
    declared_media_gap_skip: bool = False


def _pretest_completed(db: Session, student_id: int) -> bool:
    return db.query(AssessmentSession.id).filter(
        AssessmentSession.student_id == student_id,
        AssessmentSession.session_type == "pretest",
        AssessmentSession.status == "completed",
    ).first() is not None


def _core_session(
    db: Session,
    student_id: int,
    *,
    completed: Optional[bool] = None,
    level_id: Optional[int] = None,
):
    query = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student_id,
        AssessmentSession.session_type == "core",
    )
    if level_id is not None:
        query = query.filter(AssessmentSession.assigned_level == level_id)
    if completed is True:
        query = query.filter(AssessmentSession.status == "completed")
    elif completed is False:
        query = query.filter(AssessmentSession.status == "in_progress")
    return query.order_by(AssessmentSession.id.desc()).first()


def _activity_session_or_404(
    db: Session,
    session_id: int,
    student_id: int,
    *,
    require_active: bool = True,
) -> AssessmentSession:
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.student_id == student_id,
        AssessmentSession.session_type == "core",
    ).first()
    if not session or (require_active and session.status != "in_progress"):
        raise HTTPException(status_code=404, detail="جلسة التعلم غير موجودة أو انتهت")
    return session


def _step_gap(item: ContentItem, step: ContentStep) -> list[dict[str, Any]]:
    return media_gaps(item, step)


def _step_state(db: Session, attempt: Attempt, step: ContentStep) -> dict[str, Any]:
    cycle = active_verification_cycle(
        db,
        source_attempt_id=attempt.id,
        step_id=step.id,
    )
    structured = db.query(ActivityStepResponse).filter(
        ActivityStepResponse.attempt_id == attempt.id,
        ActivityStepResponse.step_id == step.id,
    ).order_by(ActivityStepResponse.attempt_no).all()

    if cycle is not None:
        verification_rows = [
            row
            for row in structured
            if (row.response_payload or {}).get("reinforcement_cycle_id") == cycle.id
            and (row.response_payload or {}).get("reinforcement_verification") is True
        ]
        if verification_rows:
            latest = verification_rows[-1]
            return {
                "done": bool(latest.is_correct),
                "attempts_used": len(verification_rows),
                "last_correct": latest.is_correct,
                "reinforcement_verification": True,
                "reinforcement_cycle_id": cycle.id,
            }
        return {
            "done": False,
            "attempts_used": 0,
            "last_correct": None,
            "reinforcement_verification": True,
            "reinforcement_cycle_id": cycle.id,
        }

    if structured:
        latest = structured[-1]
        done = bool(latest.is_correct or len(structured) >= MAX_STEP_ATTEMPTS)
        return {
            "done": done,
            "attempts_used": len(structured),
            "last_correct": latest.is_correct,
            "reinforcement_verification": False,
            "reinforcement_cycle_id": None,
        }

    response = db.query(AttemptResponse).filter(
        AttemptResponse.attempt_id == attempt.id,
        AttemptResponse.step_id == step.id,
    ).first()
    if response:
        audio = db.query(AudioSubmission).filter(
            AudioSubmission.response_id == response.id,
        ).first()
        if audio and audio.status == "rerecord_required":
            return {
                "done": False,
                "attempts_used": 1,
                "last_correct": None,
                "reinforcement_verification": False,
                "reinforcement_cycle_id": None,
            }
        return {
            "done": True,
            "attempts_used": 1,
            "last_correct": response.is_correct,
            "reinforcement_verification": False,
            "reinforcement_cycle_id": None,
        }

    return {
        "done": False,
        "attempts_used": 0,
        "last_correct": None,
        "reinforcement_verification": False,
        "reinforcement_cycle_id": None,
    }


def _step_payload(db: Session, item: ContentItem, attempt: Attempt, step: ContentStep) -> dict[str, Any]:
    state = _step_state(db, attempt, step)
    interaction = canonical_interaction(item)
    return {
        "session_id": attempt.session_id,
        "item": {
            "id": item.id,
            "stable_key": item.stable_key,
            "canonical_id": canonical_id(item),
            "title": (item.template_data or {}).get("title") or "نشاط تعليمي",
            "level_id": item.level_id,
            "order_index": item.order_index,
            "interaction_type": interaction,
            "source_method": (item.template_data or {}).get("source_method"),
            "kind": item.kind,
            "assets": item_assets(item),
        },
        "step": {
            "id": step.id,
            "order_index": step.order_index,
            "prompt_text": step.prompt_text,
            "instruction_text": instruction_text(item, step),
            "expected_reading_text": step.expected_reading_text,
            "options": [
                {"id": option.id, "text": option.text, "order_index": option.order_index}
                for option in step.options
            ],
            "assets": step_assets(item, step),
            "media_gaps": _step_gap(item, step),
        },
        "attempts_used": state["attempts_used"],
        "max_attempts": MAX_STEP_ATTEMPTS,
        "retry": state["attempts_used"] > 0 and not state["done"],
        "hint_available": state["attempts_used"] > 0 and not state["done"],
        "reinforcement_verification": state.get("reinforcement_verification", False),
        "reinforcement_cycle_id": state.get("reinforcement_cycle_id"),
    }


def _completed_core_items(db: Session, session_id: int, level_id: int) -> int:
    return (
        db.query(Attempt.id)
        .join(ContentItem, ContentItem.id == Attempt.item_id)
        .filter(
            Attempt.session_id == session_id,
            Attempt.status == "completed",
            ContentItem.kind == "core_activity",
            ContentItem.level_id == level_id,
        )
        .count()
    )


def _progress_payload(db: Session, session: AssessmentSession, level_id: int) -> dict[str, Any]:
    total = db.query(ContentItem).filter(
        ContentItem.kind == "core_activity",
        ContentItem.level_id == level_id,
    ).count()
    return {
        "session_id": session.id,
        "status": session.status,
        "level_id": level_id,
        "completed_items": _completed_core_items(db, session.id, level_id),
        "total_items": total,
        "elapsed_seconds": session.elapsed_seconds,
    }


def _finalize_attempt_if_done(db: Session, attempt: Attempt, item: ContentItem) -> None:
    for step in item.steps:
        if not _step_state(db, attempt, step)["done"]:
            return
    attempt.status = "completed"
    attempt.completed_at = datetime.now(timezone.utc)


def _finalize_session_if_done(db: Session, session: AssessmentSession, level_id: int) -> None:
    required = db.query(ContentItem).filter(
        ContentItem.kind == "core_activity",
        ContentItem.level_id == level_id,
    ).count()
    completed = _completed_core_items(db, session.id, level_id)
    if required == CORE_ACTIVITY_COUNT and completed >= required:
        session.status = "completed"
        session.completed_at = datetime.now(timezone.utc)
        session.updated_at = datetime.now(timezone.utc)


@router.get("/status")
def learning_status(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    if not _pretest_completed(db, student.id):
        return {
            "available": False,
            "reason": "pretest_required",
            "level_id": student.current_level,
            "completed_items": 0,
            "total_items": CORE_ACTIVITY_COUNT,
            "completed": False,
            "session_id": None,
        }
    session = _core_session(db, student.id)
    if not session:
        return {
            "available": True,
            "level_id": student.current_level,
            "completed_items": 0,
            "total_items": CORE_ACTIVITY_COUNT,
            "completed": False,
            "session_id": None,
        }
    level_id = session.assigned_level or student.current_level
    progress = _progress_payload(db, session, level_id)
    return {
        "available": True,
        **progress,
        "completed": session.status == "completed",
    }


@router.post("/start")
def start_learning(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    if not student.is_active:
        raise HTTPException(status_code=403, detail="حساب الطالب غير نشط")
    if not _pretest_completed(db, student.id):
        raise HTTPException(status_code=409, detail="أكمل الاختبار القبلي قبل بدء الأنشطة التعليمية")

    active_any = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.status == "in_progress",
    ).first()
    if active_any:
        if active_any.session_type == "core":
            return _progress_payload(db, active_any, active_any.assigned_level or student.current_level)
        raise HTTPException(status_code=409, detail="أكمل الاختبار الجاري أولًا")

    completed = _core_session(db, student.id, completed=True, level_id=student.current_level)
    if completed:
        return _progress_payload(db, completed, completed.assigned_level or student.current_level)

    total = db.query(ContentItem).filter(
        ContentItem.kind == "core_activity",
        ContentItem.level_id == student.current_level,
    ).count()
    if total != CORE_ACTIVITY_COUNT:
        raise HTTPException(status_code=409, detail="مجموعة الأنشطة الأساسية المعتمدة غير مكتملة")

    session = AssessmentSession(
        student_id=student.id,
        session_type="core",
        status="in_progress",
        assigned_level=student.current_level,
    )
    db.add(session)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        active = _core_session(db, student.id, completed=False)
        if active:
            return _progress_payload(db, active, active.assigned_level or student.current_level)
        raise HTTPException(status_code=409, detail="حدث تعارض أثناء بدء جلسة التعلم")
    db.refresh(session)
    return _progress_payload(db, session, student.current_level)


@router.get("/session/{session_id}/progress")
def learning_progress(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = _activity_session_or_404(db, session_id, student.id, require_active=False)
    return _progress_payload(db, session, session.assigned_level or student.current_level)


def _pending_attempt(db: Session, session_id: int):
    return db.query(Attempt).filter(
        Attempt.session_id == session_id,
        Attempt.status == "in_progress",
    ).order_by(Attempt.id).first()


def _load_item(db: Session, item_id: int):
    return db.query(ContentItem).options(
        joinedload(ContentItem.steps).joinedload(ContentStep.options),
        joinedload(ContentItem.steps).joinedload(ContentStep.assets),
        joinedload(ContentItem.assets),
    ).filter(ContentItem.id == item_id).first()


def _rich_item_query(db: Session):
    return db.query(ContentItem).options(
        joinedload(ContentItem.steps).joinedload(ContentStep.options),
        joinedload(ContentItem.steps).joinedload(ContentStep.assets),
        joinedload(ContentItem.assets),
    )


@router.get("/session/{session_id}/next")
def next_activity_step(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = _activity_session_or_404(db, session_id, student.id)

    pending_attempt = _pending_attempt(db, session.id)
    if pending_attempt:
        item = _load_item(db, pending_attempt.item_id)
        if not item:
            raise HTTPException(status_code=409, detail="تعذر تحميل محتوى النشاط")
        for step in item.steps:
            if not _step_state(db, pending_attempt, step)["done"]:
                return _step_payload(db, item, pending_attempt, step)
        _finalize_attempt_if_done(db, pending_attempt, item)
        db.commit()

    from adaptation_runtime import prepare_next_for_student

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

    db.refresh(session)
    db.refresh(student)
    level_id = session.assigned_level or student.current_level

    pending_attempt = _pending_attempt(db, session.id)
    if pending_attempt:
        item = _load_item(db, pending_attempt.item_id)
        if not item:
            raise HTTPException(status_code=409, detail="تعذر تحميل نشاط التقوية أو التحقق")
        first_pending = next(
            (step for step in item.steps if not _step_state(db, pending_attempt, step)["done"]),
            None,
        )
        if first_pending:
            return _step_payload(db, item, pending_attempt, first_pending)
        _finalize_attempt_if_done(db, pending_attempt, item)
        db.commit()

    completed_ids = [
        row.item_id
        for row in db.query(Attempt.item_id).filter(
            Attempt.session_id == session.id,
            Attempt.status == "completed",
        ).all()
    ]
    query = _rich_item_query(db).filter(
        ContentItem.kind == "core_activity",
        ContentItem.level_id == level_id,
    )
    if completed_ids:
        query = query.filter(ContentItem.id.notin_(completed_ids))
    item = query.order_by(ContentItem.order_index).first()
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
    return _step_payload(db, item, attempt, first_step)


def _score_submission(item: ContentItem, step: ContentStep, option_ids: list[int]) -> bool:
    ordered = sorted(step.options, key=lambda option: option.order_index)
    valid_ids = {option.id for option in ordered}
    if not option_ids or any(option_id not in valid_ids for option_id in option_ids):
        raise HTTPException(status_code=400, detail="الإجابة تحتوي على خيار لا ينتمي إلى هذه الجولة")
    if len(set(option_ids)) != len(option_ids):
        raise HTTPException(status_code=400, detail="لا يمكن اختيار العنصر نفسه أكثر من مرة")

    interaction = canonical_interaction(item)
    if interaction in {"choose_one", "listen_choose_one", "choose_image", "listen_choose_image"}:
        if len(option_ids) != 1:
            raise HTTPException(status_code=400, detail="اختر إجابة واحدة فقط")
        correct = next((option.id for option in ordered if option.is_correct), None)
        return option_ids[0] == correct

    if interaction in {"choose_many", "listen_choose_many"}:
        if len(ordered) < 2:
            raise HTTPException(status_code=409, detail="جولة الاختيار المتعدد المعتمدة غير مكتملة")
        # Accepted content seeding preserves the two target items in positions
        # one and two for the multi-select rounds.
        expected = {ordered[0].id, ordered[1].id}
        return set(option_ids) == expected and len(option_ids) == len(expected)

    if interaction in {"sequence", "memory_sequence", "path_sequence", "build_word"}:
        expected = [option.id for option in ordered]
        return option_ids == expected

    raise HTTPException(status_code=400, detail="نوع هذا النشاط غير مدعوم حاليًا")


@router.post("/session/{session_id}/attempt/{item_id}/submit")
def submit_activity_step(
    session_id: int,
    item_id: int,
    body: ActivitySubmitRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    idempotency_key = _validate_idempotency_key(idempotency_key)
    session = _activity_session_or_404(db, session_id, student.id)
    operation = f"activity.answer:{session_id}:{item_id}:{body.step_id}"
    request_hash = _request_hash(body.model_dump(mode="json"))
    replay = _idempotency_replay(db, student.id, operation, idempotency_key, request_hash)
    if replay is not None:
        return replay

    attempt = db.query(Attempt).filter(
        Attempt.session_id == session.id,
        Attempt.item_id == item_id,
        Attempt.status == "in_progress",
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="لا توجد محاولة نشطة لهذا النشاط")

    item = _load_item(db, item_id)
    step = next((candidate for candidate in item.steps if candidate.id == body.step_id), None) if item else None
    if not item or not step:
        raise HTTPException(status_code=400, detail="الجولة لا تنتمي إلى هذا النشاط")

    interaction = canonical_interaction(item)
    if interaction in {"read_aloud", "timed_read_aloud"}:
        raise HTTPException(status_code=400, detail="استخدم مسار التسجيل الصوتي لجولة القراءة الجهرية")

    verification_cycle = active_verification_cycle(
        db,
        source_attempt_id=attempt.id,
        step_id=step.id,
    )
    previous = db.query(ActivityStepResponse).filter(
        ActivityStepResponse.attempt_id == attempt.id,
        ActivityStepResponse.step_id == step.id,
    ).order_by(ActivityStepResponse.attempt_no).all()

    if verification_cycle is None:
        if previous and (previous[-1].is_correct or len(previous) >= MAX_STEP_ATTEMPTS):
            raise HTTPException(status_code=409, detail="هذه الجولة مكتملة بالفعل؛ أعد تحميل الصفحة للمتابعة")
    else:
        verification_used = verification_response_count(
            db,
            cycle=verification_cycle,
            step_id=step.id,
        )
        if verification_used >= verification_cycle.max_verification_rounds:
            raise HTTPException(status_code=409, detail="اكتملت محاولات التحقق لهذه المهارة")
        if body.declared_media_gap_skip:
            raise HTTPException(
                status_code=409,
                detail="لا يمكن اعتماد تخطي وسائط كدليل تحقق بعد نشاط التقوية",
            )

    gaps = _step_gap(item, step)
    if body.declared_media_gap_skip:
        if not gaps:
            raise HTTPException(status_code=400, detail="هذه الجولة لا تحتوي على فجوة وسائط معلنة")
        is_correct = True
        payload = {"declared_media_gap_skip": True, "gaps": gaps}
    else:
        is_correct = _score_submission(item, step, body.selected_option_ids)
        payload = {"selected_option_ids": body.selected_option_ids}

    if verification_cycle is not None:
        payload = {
            **payload,
            "reinforcement_verification": True,
            "reinforcement_cycle_id": verification_cycle.id,
        }

    response = ActivityStepResponse(
        attempt_id=attempt.id,
        step_id=step.id,
        attempt_no=len(previous) + 1,
        response_payload=payload,
        is_correct=is_correct,
        hint_used=body.hint_used,
        elapsed_seconds=body.elapsed_seconds,
    )
    db.add(response)
    attempt.elapsed_seconds += body.elapsed_seconds
    session.elapsed_seconds += body.elapsed_seconds
    session.updated_at = datetime.now(timezone.utc)
    db.flush()

    if verification_cycle is not None:
        verification_status = finish_verification_step(
            db,
            cycle=verification_cycle,
            step_id=step.id,
            is_correct=is_correct,
        )
        verification_used = verification_response_count(
            db,
            cycle=verification_cycle,
            step_id=step.id,
        )
        complete = bool(is_correct or verification_status == "escalated")
        show_hint = bool(not is_correct and verification_status == "verification_pending")
        attempts_used = verification_used
    else:
        verification_status = None
        attempts_used = len(previous) + 1
        complete = bool(is_correct or attempts_used >= MAX_STEP_ATTEMPTS)
        show_hint = bool(not is_correct and attempts_used < MAX_STEP_ATTEMPTS)

    _finalize_attempt_if_done(db, attempt, item)

    response_json = {
        "status": "ok",
        "is_correct": is_correct,
        "attempts_used": attempts_used,
        "step_complete": complete,
        "show_hint": show_hint,
        "activity_complete": attempt.status == "completed",
        "reinforcement_verification": verification_cycle is not None,
        "verification_status": verification_status,
        # Session completion is deliberately finalized by GET /next after P06
        # evaluates the newly completed attempt. This prevents false posttest
        # unlocks before support/transition logic runs.
        "learning_complete": False,
    }
    _store_idempotency(db, student.id, operation, idempotency_key, request_hash, response_json)
    return _commit_idempotent(
        db,
        student.id,
        operation,
        idempotency_key,
        request_hash,
        response_json,
    )
