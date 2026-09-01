"""Student-facing presentation metadata for the current learning round.

Scoring and adaptive decisions remain owned by activities.py. This endpoint only
projects the approved 2026-09-01 learning-experience metadata so the web client
can render the correct question, encouragement/hint, round number and memory
preview without parsing source-document prose.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from activities import _activity_session_or_404, _step_state
from content_runtime import canonical_interaction, item_assets, step_assets
from db.models import Attempt, ContentItem, ContentStep, Student
from dependencies import get_current_student, get_db

router = APIRouter(prefix="/learning-experience", tags=["Learning Experience"])
VERSION = "HIMMA-LEARNING-2026-09-01"


@router.get("/session/{session_id}")
def current_learning_experience(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = _activity_session_or_404(db, session_id, student.id, require_active=False)
    attempt = (
        db.query(Attempt)
        .filter(Attempt.session_id == session.id, Attempt.status == "in_progress")
        .order_by(Attempt.id.desc())
        .first()
    )
    if attempt is None:
        return None
    item = (
        db.query(ContentItem)
        .options(
            joinedload(ContentItem.steps).joinedload(ContentStep.options),
            joinedload(ContentItem.steps).joinedload(ContentStep.assets),
            joinedload(ContentItem.assets),
        )
        .filter(ContentItem.id == attempt.item_id)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=409, detail="تعذر تحميل بيانات عرض النشاط")

    steps = sorted(item.steps, key=lambda value: value.order_index)
    step = next((value for value in steps if not _step_state(db, attempt, value)["done"]), None)
    if step is None:
        return None

    data = item.template_data or {}
    experience = data.get("learning_experience") or {}
    if data.get("learning_experience_version") != VERSION:
        raise HTTPException(status_code=409, detail="بيانات عرض النشاط تحتاج إلى تحديث")
    rounds = experience.get("rounds") or []
    round_data = next(
        (value for value in rounds if int(value.get("round_number") or 0) == int(step.order_index)),
        None,
    )
    if not round_data:
        raise HTTPException(status_code=409, detail="تعذر العثور على بيانات الجولة الحالية")

    state = _step_state(db, attempt, step)
    return {
        "version": VERSION,
        "item_id": item.id,
        "stable_key": item.stable_key,
        "kind": item.kind,
        "interaction_type": canonical_interaction(item),
        "round": round_data,
        "retry": state["attempts_used"] > 0 and not state["done"],
        "assets": item_assets(item),
        "step_assets": step_assets(item, step),
    }
