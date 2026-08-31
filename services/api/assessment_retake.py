"""Supervisor-authorized pre/post retakes with preserved assessment history.

This router owns ``POST /assessment/start`` and the assessment completion bridge
ahead of the legacy routers. Initial assessments keep the existing journey gates.
A completed assessment can only be started again when a supervisor has created a
pending retake authorization with a written reason.

Answer-key review remains separate: authorization does not expose correct
answers to the student and does not delete or rewrite any prior attempt.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import schemas
from db.models import (
    AssessmentRetakeAuthorization,
    AssessmentSession,
    AuditLog,
    Student,
    User,
)
from dependencies import get_current_student, get_current_user, get_db
from journey import build_journey_summary

router = APIRouter(tags=["Assessment Retakes"])


class RetakeAuthorizationRequest(BaseModel):
    session_type: Literal["pretest", "posttest"]
    reason: str = Field(min_length=5, max_length=1000)


class RetakeAuthorizationResponse(BaseModel):
    id: int
    student_id: int
    session_type: str
    previous_session_id: int
    authorized_by: int
    reason: str
    status: str
    created_at: datetime
    consumed_at: datetime | None = None
    new_session_id: int | None = None


class AssessmentAttemptSummary(BaseModel):
    id: int
    session_type: str
    attempt_no: int
    status: str
    final_score: float | None
    assigned_level: int | None
    started_at: datetime
    completed_at: datetime | None
    supersedes_session_id: int | None
    official_for_reporting: bool


def _audit(
    db: Session,
    *,
    actor_id: int,
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict | None = None,
) -> None:
    db.add(AuditLog(
        actor_role="researcher",
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=json.dumps(details, ensure_ascii=False, sort_keys=True) if details else None,
    ))


def _latest_completed(db: Session, student_id: int, session_type: str) -> AssessmentSession | None:
    return (
        db.query(AssessmentSession)
        .filter(
            AssessmentSession.student_id == student_id,
            AssessmentSession.session_type == session_type,
            AssessmentSession.status == "completed",
        )
        .order_by(AssessmentSession.assessment_attempt_no.desc(), AssessmentSession.id.desc())
        .first()
    )


def _pending_authorization(
    db: Session,
    student_id: int,
    session_type: str,
) -> AssessmentRetakeAuthorization | None:
    return (
        db.query(AssessmentRetakeAuthorization)
        .filter(
            AssessmentRetakeAuthorization.student_id == student_id,
            AssessmentRetakeAuthorization.session_type == session_type,
            AssessmentRetakeAuthorization.status == "pending",
        )
        .order_by(AssessmentRetakeAuthorization.id.desc())
        .first()
    )


def _assert_posttest_gate(db: Session, student: Student) -> None:
    pretest_completed = _latest_completed(db, student.id, "pretest") is not None
    if not pretest_completed:
        raise HTTPException(status_code=409, detail="أكمل الاختبار القبلي أولًا")
    if not student.posttest_enabled:
        raise HTTPException(status_code=403, detail="لم يفتح المشرف الاختبار البعدي بعد")
    journey = build_journey_summary(db, student)
    if not journey["learning_journey_completed"]:
        raise HTTPException(status_code=409, detail="رحلة التعلم غير مكتملة بعد")


def _attempt_payload(session: AssessmentSession) -> AssessmentAttemptSummary:
    return AssessmentAttemptSummary(
        id=session.id,
        session_type=session.session_type,
        attempt_no=session.assessment_attempt_no,
        status=session.status,
        final_score=float(session.final_score) if session.final_score is not None else None,
        assigned_level=session.assigned_level,
        started_at=session.started_at,
        completed_at=session.completed_at,
        supersedes_session_id=session.supersedes_session_id,
        official_for_reporting=bool(session.official_for_reporting),
    )


def mark_official_completed_attempt(db: Session, session: AssessmentSession) -> None:
    """Make one completed pre/post attempt authoritative without deleting history."""
    if session.session_type not in {"pretest", "posttest"} or session.status != "completed":
        return
    db.query(AssessmentSession).filter(
        AssessmentSession.student_id == session.student_id,
        AssessmentSession.session_type == session.session_type,
        AssessmentSession.id != session.id,
    ).update({AssessmentSession.official_for_reporting: False}, synchronize_session=False)
    session.official_for_reporting = True


@router.post(
    "/researcher/students/{student_id}/assessment-retakes",
    response_model=RetakeAuthorizationResponse,
)
def authorize_assessment_retake(
    student_id: int,
    body: RetakeAuthorizationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.id == student_id).with_for_update().first()
    if not student:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")

    active = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.status == "in_progress",
    ).first()
    if active:
        raise HTTPException(status_code=409, detail="يجب إنهاء الجلسة الحالية قبل السماح بإعادة الاختبار")

    previous = _latest_completed(db, student.id, body.session_type)
    if previous is None:
        raise HTTPException(status_code=409, detail="لا توجد محاولة مكتملة يمكن إعادة هذا الاختبار بعدها")
    if _pending_authorization(db, student.id, body.session_type):
        raise HTTPException(status_code=409, detail="يوجد إذن إعادة اختبار معلّق بالفعل")

    authorization = AssessmentRetakeAuthorization(
        student_id=student.id,
        session_type=body.session_type,
        previous_session_id=previous.id,
        authorized_by=user.id,
        reason=body.reason.strip(),
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    db.add(authorization)
    db.flush()
    _audit(
        db,
        actor_id=user.id,
        action="assessment.retake.authorize",
        entity_type="assessment_retake_authorization",
        entity_id=str(authorization.id),
        details={
            "student_id": student.id,
            "session_type": body.session_type,
            "previous_session_id": previous.id,
            "previous_attempt_no": previous.assessment_attempt_no,
            "reason": authorization.reason,
        },
    )
    db.commit()
    db.refresh(authorization)
    return authorization


@router.get(
    "/researcher/students/{student_id}/assessment-attempts",
    response_model=list[AssessmentAttemptSummary],
)
def assessment_attempt_history(
    student_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not db.query(Student.id).filter(Student.id == student_id).first():
        raise HTTPException(status_code=404, detail="الطالب غير موجود")
    sessions = (
        db.query(AssessmentSession)
        .filter(
            AssessmentSession.student_id == student_id,
            AssessmentSession.session_type.in_(["pretest", "posttest"]),
        )
        .order_by(
            AssessmentSession.session_type,
            AssessmentSession.assessment_attempt_no,
            AssessmentSession.id,
        )
        .all()
    )
    return [_attempt_payload(session) for session in sessions]


@router.post("/assessment/start", response_model=schemas.AssessmentSessionResponse)
def start_assessment_with_retake_policy(
    request: schemas.AssessmentStartRequest,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    if not student.is_active:
        raise HTTPException(status_code=403, detail="حساب الطالب غير نشط")

    active = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.status == "in_progress",
    ).first()
    if active:
        if active.session_type == request.session_type:
            return active
        raise HTTPException(status_code=409, detail="أكمل الجلسة الحالية أولًا")

    previous = _latest_completed(db, student.id, request.session_type)
    authorization = None
    attempt_no = 1
    supersedes_session_id = None

    if previous is not None:
        authorization = _pending_authorization(db, student.id, request.session_type)
        if authorization is None:
            raise HTTPException(status_code=409, detail="هذا الاختبار مكتمل بالفعل، ويحتاج إذن إعادة من المشرف")
        if authorization.previous_session_id != previous.id:
            raise HTTPException(status_code=409, detail="إذن إعادة الاختبار لا يطابق آخر محاولة مكتملة")
        attempt_no = previous.assessment_attempt_no + 1
        supersedes_session_id = previous.id

    if request.session_type == "posttest":
        _assert_posttest_gate(db, student)

    new_session = AssessmentSession(
        student_id=student.id,
        session_type=request.session_type,
        status="in_progress",
        assessment_attempt_no=attempt_no,
        supersedes_session_id=supersedes_session_id,
        official_for_reporting=False,
    )
    db.add(new_session)
    try:
        db.flush()
        if authorization is not None:
            authorization.status = "consumed"
            authorization.consumed_at = datetime.now(timezone.utc)
            authorization.new_session_id = new_session.id
        db.commit()
    except IntegrityError:
        db.rollback()
        active = db.query(AssessmentSession).filter(
            AssessmentSession.student_id == student.id,
            AssessmentSession.status == "in_progress",
        ).first()
        if active and active.session_type == request.session_type:
            return active
        raise HTTPException(status_code=409, detail="تعذر بدء الاختبار بسبب تعارض في الجلسة")
    db.refresh(new_session)
    return new_session


@router.post("/assessment/session/{session_id}/finish")
def finish_assessment_and_select_official_attempt(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    # Import lazily to avoid an import cycle: temporary_audio_skip imports the
    # legacy assessment module, while this bridge must execute before both routes.
    from temporary_audio_skip import finish_assessment_with_optional_temporary_skips

    result = finish_assessment_with_optional_temporary_skips(
        session_id=session_id,
        db=db,
        student=student,
    )
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.student_id == student.id,
    ).one()
    mark_official_completed_attempt(db, session)
    db.commit()
    return result
