"""Canonical adaptive-learning activity router.

The Stage-2 module remains a service library for proven scoring/state helpers,
but it is not mounted as a second router. All public /activities routes have one
owner here, so correctness never depends on FastAPI registration order.

Guarantees:
- a closed historical level session is never used for a new submission;
- clients holding the previous level URL are safely bridged to the one active
  Core session, including refresh/resume after promotion;
- normal Core selection prioritizes missing/weak critical-skill evidence from
  the active session only and uses order_index as a deterministic tie-breaker;
- status/start/progress/next/submit each have a single mounted route.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from activities import (
    ActivitySubmitRequest,
    _activity_session_or_404,
    _finalize_attempt_if_done,
    _finalize_session_if_done,
    _load_item,
    _pending_attempt,
    _progress_payload,
    _rich_item_query,
    _step_payload,
    _step_state,
    learning_status as stage2_learning_status,
    start_learning as stage2_start_learning,
    submit_activity_step as stage2_submit_activity_step,
)
from adaptation import _load_policy, _valid_signals
from adaptation_runtime import prepare_next_for_student
from db.models import AssessmentSession, Attempt, ContentItem, Skill, Student
from dependencies import get_current_student, get_db

router = APIRouter(tags=["Activities"])


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


def _active_core_session(db: Session, student_id: int) -> AssessmentSession | None:
    return (
        db.query(AssessmentSession)
        .filter(
            AssessmentSession.student_id == student_id,
            AssessmentSession.session_type == "core",
            AssessmentSession.status == "in_progress",
        )
        .order_by(AssessmentSession.id.desc())
        .first()
    )


def _resolve_active_session(
    db: Session,
    *,
    requested_session_id: int,
    student_id: int,
) -> AssessmentSession:
    """Resolve a historical route id to the student's current Core session.

    This keeps an already-open browser route usable across an early promotion
    without mutating or relabelling the completed historical session.
    """
    requested = _activity_session_or_404(
        db,
        requested_session_id,
        student_id,
        require_active=False,
    )
    if requested.status == "in_progress":
        return requested
    active = _active_core_session(db, student_id)
    if active is None:
        raise HTTPException(status_code=404, detail="جلسة التعلم غير موجودة أو انتهت")
    return active


def _preferred_core_skill_id(
    db: Session,
    *,
    student_id: int,
    session_id: int,
    level_id: int,
) -> int | None:
    """Choose a configured critical skill needing evidence in this session."""
    policy = _load_policy()
    codes = [
        str(code)
        for code in policy.get("critical_skill_codes_by_level", {}).get(str(level_id), [])
        if str(code).strip()
    ]
    if not codes:
        return None

    skills = db.query(Skill).filter(
        Skill.level_id == level_id,
        Skill.canonical_skill_id.in_(codes),
    ).all()
    by_code = {skill.canonical_skill_id: skill for skill in skills}
    if any(code not in by_code for code in codes):
        return None

    latest_by_skill: dict[int, float] = {}
    for signal in _valid_signals(db, student_id, level_id, session_id=session_id):
        latest_by_skill[signal.skill_id] = signal.score

    for code in codes:
        skill_id = by_code[code].id
        if skill_id not in latest_by_skill:
            return skill_id

    return min(
        (by_code[code].id for code in codes),
        key=lambda skill_id: (latest_by_skill[skill_id], skill_id),
    )


def _next_unused_core_item(
    db: Session,
    *,
    student_id: int,
    session_id: int,
    level_id: int,
) -> ContentItem | None:
    completed_ids = {
        row[0]
        for row in db.query(Attempt.item_id).filter(
            Attempt.session_id == session_id,
            Attempt.status == "completed",
        ).all()
    }
    base = _rich_item_query(db).filter(
        ContentItem.kind == "core_activity",
        ContentItem.level_id == level_id,
        ContentItem.status == "approved",
    )
    if completed_ids:
        base = base.filter(ContentItem.id.notin_(completed_ids))

    target_skill_id = _preferred_core_skill_id(
        db,
        student_id=student_id,
        session_id=session_id,
        level_id=level_id,
    )
    if target_skill_id is not None:
        preferred = base.filter(ContentItem.skill_id == target_skill_id).order_by(
            ContentItem.order_index,
            ContentItem.id,
        ).first()
        if preferred is not None:
            return preferred

    return base.order_by(ContentItem.order_index, ContentItem.id).first()


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
            if not _step_state(db, pending_attempt, step)["done"]:
                return _step_payload(db, item, pending_attempt, step)
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
            (step for step in item.steps if not _step_state(db, pending_attempt, step)["done"]),
            None,
        )
        if first_pending:
            return _step_payload(db, item, pending_attempt, first_pending)
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
    return _step_payload(db, item, attempt, first_step)


@router.post("/activities/session/{session_id}/attempt/{item_id}/submit")
def submit_activity_step(
    session_id: int,
    item_id: int,
    body: ActivitySubmitRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = _resolve_active_session(
        db,
        requested_session_id=session_id,
        student_id=student.id,
    )
    return stage2_submit_activity_step(
        session_id=session.id,
        item_id=item_id,
        body=body,
        idempotency_key=idempotency_key,
        db=db,
        student=student,
    )
