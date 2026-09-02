"""Clean DB-only read contract for pretest/posttest student screens.

The assessment engine remains responsible for attempts, scoring and idempotency.
This router only transforms the engine's next-item selection into an explicit
student-facing payload. Legacy prompt_text/template_data are never exposed.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import assessment
import schemas
from content_runtime import canonical_id, canonical_interaction, item_assets, step_assets, media_gaps
from db.models import ContentItem, ContentStep, Student
from dependencies import get_current_student, get_db

router = APIRouter(prefix="/assessment-view", tags=["Assessment Student View"])

SINGLE = {"choose_one", "listen_choose_one", "choose_image", "listen_choose_image"}
MULTI = {"choose_many", "listen_choose_many"}
ORDER = {"sequence", "memory_sequence", "path_sequence", "build_word"}


def _presentation(item: ContentItem) -> dict:
    data = item.template_data or {}
    key = "pretest_experience" if item.kind == "pretest_question" else "posttest_experience" if item.kind == "posttest_question" else ""
    value = dict(data.get(key) or {}) if key else {}
    required = {
        "version", "question_number", "section", "skill", "encouragement",
        "question_text", "instruction_text", "interaction_type",
    }
    missing = sorted(name for name in required if value.get(name) in {None, ""})
    if missing:
        raise HTTPException(status_code=409, detail=f"بيانات عرض السؤال غير مكتملة: {', '.join(missing)}")
    value.setdefault("stimulus", {"kind": "none"})
    return value


def _selection_count(item: ContentItem, step: ContentStep) -> int:
    interaction = canonical_interaction(item)
    if interaction in SINGLE:
        return 1
    if interaction in MULTI:
        return len([option for option in step.options if option.is_correct])
    if interaction in ORDER:
        return len(assessment._expected_order_ids(item, step))
    return 0


def _clean_payload(item: ContentItem, step: ContentStep) -> dict:
    presentation = _presentation(item)
    interaction = canonical_interaction(item)
    if str(presentation.get("interaction_type")) != interaction:
        raise HTTPException(status_code=409, detail="نوع التفاعل لا يطابق بيانات عرض السؤال")
    return {
        "id": item.id,
        "stable_key": item.stable_key,
        "canonical_id": canonical_id(item),
        "kind": item.kind,
        "interaction_type": interaction,
        "title": str(presentation.get("skill") or "مهمة تعليمية"),
        "presentation": presentation,
        "item_assets": item_assets(item),
        "steps": [{
            "id": step.id,
            "order_index": step.order_index,
            "expected_reading_text": step.expected_reading_text,
            "required_selection_count": _selection_count(item, step),
            "options": [
                {"id": option.id, "text": option.text, "order_index": option.order_index}
                for option in sorted(step.options, key=lambda value: value.order_index)
            ],
            "assets": step_assets(item, step),
            "media_gaps": media_gaps(item, step),
        }],
    }


@router.get("/session/{session_id}/next", response_model=schemas.ContentItemResponse | None)
def next_student_view(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    raw = assessment.get_next_item(session_id=session_id, db=db, student=student)
    if raw is None:
        return None
    item_id = int(raw["id"])
    step_id = int(raw["steps"][0]["id"])
    item = assessment._load_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=409, detail="تعذر تحميل محتوى السؤال")
    step = next((value for value in item.steps if value.id == step_id), None)
    if step is None:
        raise HTTPException(status_code=409, detail="تعذر تحميل جولة السؤال")
    return _clean_payload(item, step)
