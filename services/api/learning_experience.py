"""Authoritative student-facing learning view payload.

This endpoint is the single read source for the learning screen. Academic scoring
and adaptive execution remain owned by activities.py; this endpoint exposes only
approved structured presentation data plus the exact options/media needed to
render the current round. The client must never parse legacy prompt_text.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from activities import _activity_session_or_404, _step_state
from content_runtime import canonical_interaction, item_assets, media_gaps, step_assets
from db.models import Attempt, ContentItem, ContentStep, Student
from dependencies import get_current_student, get_db

router = APIRouter(prefix="/learning-experience", tags=["Learning Experience"])
VERSION = "HIMMA-LEARNING-2026-09-01-R2"
MAX_STEP_ATTEMPTS = 2


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
    if data.get("learning_experience_version") != VERSION:
        raise HTTPException(status_code=409, detail="بيانات عرض النشاط تحتاج إلى تحديث")
    experience = data.get("learning_experience") or {}
    round_data = next(
        (
            value
            for value in (experience.get("rounds") or [])
            if int(value.get("round_number") or 0) == int(step.order_index)
        ),
        None,
    )
    if not round_data:
        raise HTTPException(status_code=409, detail="تعذر العثور على بيانات الجولة الحالية")

    state = _step_state(db, attempt, step)
    interaction = canonical_interaction(item)
    return {
        "version": VERSION,
        "session_id": session.id,
        "level_id": item.level_id,
        "item_id": item.id,
        "stable_key": item.stable_key,
        "kind": item.kind,
        "interaction_type": interaction,
        "round": round_data,
        "retry": state["attempts_used"] > 0 and not state["done"],
        "attempts_used": state["attempts_used"],
        "max_attempts": MAX_STEP_ATTEMPTS,
        "step": {
            "id": step.id,
            "order_index": step.order_index,
            "expected_reading_text": step.expected_reading_text,
            "options": [
                {"id": option.id, "text": option.text, "order_index": option.order_index}
                for option in sorted(step.options, key=lambda value: value.order_index)
            ],
            "assets": step_assets(item, step),
            "media_gaps": media_gaps(item, step),
        },
        "assets": item_assets(item),
    }
