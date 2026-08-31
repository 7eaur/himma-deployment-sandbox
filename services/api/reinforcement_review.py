"""Supervisor resolution for adaptive reinforcement gaps.

The approved catalog contains five reinforcement activities per level, but not a
one-to-one activity for every core skill. The system must never invent content or
silently choose an unrelated activity. When exact automatic matching cannot be
made, this router exposes only approved same-level reinforcement activities and
requires a supervisor to choose one with a documented reason.
"""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from db.adaptation_models import AdaptationDecision
from db.models import AssessmentSession, Attempt, AuditLog, ContentItem, Student, User
from dependencies import get_current_user, get_db

router = APIRouter(prefix="/researcher/students", tags=["Reinforcement Review"])


class ReinforcementAssignmentRequest(BaseModel):
    item_id: int = Field(gt=0)
    reason: str = Field(min_length=5, max_length=1000)


def _student_or_404(db: Session, student_id: int) -> Student:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")
    return student


def _active_core_session(db: Session, student_id: int) -> AssessmentSession:
    session = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student_id,
        AssessmentSession.session_type == "core",
        AssessmentSession.status == "in_progress",
    ).order_by(AssessmentSession.id.desc()).first()
    if not session:
        raise HTTPException(status_code=409, detail="لا توجد جلسة تعلم نشطة تحتاج إلى معالجة")
    return session


def _pending_mapping_decision(db: Session, student_id: int) -> AdaptationDecision:
    decision = db.query(AdaptationDecision).filter(
        AdaptationDecision.student_id == student_id,
        AdaptationDecision.decision_source == "automatic",
    ).order_by(AdaptationDecision.id.desc()).first()
    explanation = dict(decision.explanation or {}) if decision else {}
    if not decision or not explanation.get("mapping_gap"):
        raise HTTPException(status_code=409, detail="لا توجد فجوة تقوية معلقة لهذا الطالب")
    return decision


def _option_payload(db: Session, session: AssessmentSession, item: ContentItem) -> dict:
    attempt = db.query(Attempt).filter(
        Attempt.session_id == session.id,
        Attempt.item_id == item.id,
    ).first()
    template = item.template_data or {}
    return {
        "item_id": item.id,
        "canonical_id": template.get("canonical_id"),
        "title": template.get("title") or "نشاط تقوية",
        "skill_id": item.skill_id,
        "skill_name": item.skill.name if item.skill else None,
        "interaction_type": item.interaction_type,
        "already_used": attempt is not None,
        "attempt_status": attempt.status if attempt else None,
    }


@router.get("/{student_id}/adaptation/reinforcement-options")
def reinforcement_options(
    student_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _student_or_404(db, student_id)
    session = _active_core_session(db, student_id)
    decision = _pending_mapping_decision(db, student_id)
    level_id = session.assigned_level or decision.new_level
    items = (
        db.query(ContentItem)
        .options(joinedload(ContentItem.skill))
        .filter(
            ContentItem.kind == "reinforcement_activity",
            ContentItem.level_id == level_id,
        )
        .order_by(ContentItem.order_index)
        .all()
    )
    return {
        "student_id": student_id,
        "level_id": level_id,
        "weakest_skill_id": decision.weakest_skill_id,
        "decision_id": decision.id,
        "options": [_option_payload(db, session, item) for item in items],
    }


@router.post("/{student_id}/adaptation/assign-reinforcement")
def assign_reinforcement(
    student_id: int,
    body: ReinforcementAssignmentRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.id == student_id).with_for_update().first()
    if not student:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")
    session = _active_core_session(db, student_id)
    decision = _pending_mapping_decision(db, student_id)
    level_id = session.assigned_level or decision.new_level

    item = db.query(ContentItem).filter(
        ContentItem.id == body.item_id,
        ContentItem.kind == "reinforcement_activity",
        ContentItem.level_id == level_id,
    ).first()
    if not item:
        raise HTTPException(status_code=422, detail="اختر نشاط تقوية معتمدًا من المستوى الحالي")

    existing = db.query(Attempt).filter(
        Attempt.session_id == session.id,
        Attempt.item_id == item.id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="نشاط التقوية المحدد استُخدم بالفعل في هذه الجلسة")

    explanation = dict(decision.explanation or {})
    original_gap = explanation.get("mapping_gap")
    explanation.pop("mapping_gap", None)
    explanation["manual_reinforcement_resolution"] = {
        "item_id": item.id,
        "resolved_by": user.id,
        "resolved_at": datetime.now(timezone.utc).isoformat(),
        "original_gap": original_gap,
    }
    decision.explanation = explanation
    decision.recommended_item_id = item.id

    attempt = Attempt(session_id=session.id, item_id=item.id, status="in_progress")
    db.add(attempt)
    db.flush()

    manual = AdaptationDecision(
        student_id=student.id,
        decision_source="manual",
        action="override",
        mastery_score=None,
        previous_level=student.current_level,
        new_level=student.current_level,
        weakest_skill_id=decision.weakest_skill_id,
        recommended_item_id=item.id,
        valid_attempt_count=decision.valid_attempt_count,
        consecutive_low_count=decision.consecutive_low_count,
        snapshot_key=None,
        explanation={
            "reason": "supervisor_reinforcement_assignment",
            "automatic_decision_id": decision.id,
            "selected_item_id": item.id,
        },
        manual_reason=body.reason.strip(),
        actor_id=user.id,
    )
    db.add(manual)
    db.add(AuditLog(
        actor_role="researcher",
        actor_id=user.id,
        action="adaptation.reinforcement.assign",
        entity_type="student",
        entity_id=str(student.id),
        details=json.dumps(
            {
                "automatic_decision_id": decision.id,
                "reinforcement_item_id": item.id,
                "level_id": level_id,
                "reason": body.reason.strip(),
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
    ))
    db.commit()
    db.refresh(attempt)
    db.refresh(manual)

    return {
        "message": "تم إسناد نشاط التقوية المعتمد للطالب",
        "attempt_id": attempt.id,
        "item_id": item.id,
        "manual_decision_id": manual.id,
        "level_id": level_id,
    }
