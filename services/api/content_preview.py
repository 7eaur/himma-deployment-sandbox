"""Read-only supervisor feed for the temporary student-experience preview.

The preview intentionally does not create sessions, attempts, responses, audio
submissions, adaptation decisions, or rewards. It exposes the same DB-backed
presentation metadata and media URLs used by the student runtime so supervisors
can walk the approved content in a deterministic section order without changing
any student result.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from content_runtime import (
    canonical_id,
    canonical_interaction,
    item_assets,
    media_gaps,
    presentation_data,
    step_assets,
)
from db.models import ContentItem, ContentStep, User
from dependencies import get_current_user, get_db

router = APIRouter(prefix="/researcher/content-preview", tags=["Supervisor Content Preview"])

SINGLE = {"choose_one", "listen_choose_one", "choose_image", "listen_choose_image"}
MULTI = {"choose_many", "listen_choose_many"}
ORDER = {"sequence", "memory_sequence", "path_sequence", "build_word"}

SECTION_SPECS = (
    ("pretest", "الاختبار القبلي", "pretest_question", None),
    ("level-1-core", "المستوى الأول", "core_activity", 1),
    ("level-1-reinforcement", "تقوية المستوى الأول", "reinforcement_activity", 1),
    ("level-2-core", "المستوى الثاني", "core_activity", 2),
    ("level-2-reinforcement", "تقوية المستوى الثاني", "reinforcement_activity", 2),
    ("level-3-core", "المستوى الثالث", "core_activity", 3),
    ("level-3-reinforcement", "تقوية المستوى الثالث", "reinforcement_activity", 3),
    ("posttest", "الاختبار البعدي", "posttest_question", None),
)


def _required_selection_count(interaction: str, step: ContentStep) -> int:
    if interaction in SINGLE:
        return 1
    if interaction in MULTI:
        return len([option for option in step.options if option.is_correct])
    if interaction in ORDER:
        return len(step.options)
    return 0


def _step_payload(item: ContentItem, step: ContentStep) -> dict:
    interaction = canonical_interaction(item)
    return {
        "id": step.id,
        "order_index": step.order_index,
        "expected_reading_text": step.expected_reading_text,
        "required_selection_count": _required_selection_count(interaction, step),
        "presentation": presentation_data(item, step),
        "options": [
            {
                "id": option.id,
                "text": option.text,
                "order_index": option.order_index,
            }
            for option in sorted(step.options, key=lambda value: value.order_index)
        ],
        "assets": step_assets(item, step),
        "media_gaps": media_gaps(item, step),
    }


def _item_payload(item: ContentItem) -> dict:
    return {
        "id": item.id,
        "stable_key": item.stable_key,
        "canonical_id": canonical_id(item),
        "kind": item.kind,
        "level_id": item.level_id,
        "order_index": item.order_index,
        "interaction_type": canonical_interaction(item),
        "skill": item.skill.name if item.skill is not None else None,
        "item_assets": item_assets(item),
        "steps": [
            _step_payload(item, step)
            for step in sorted(item.steps, key=lambda value: value.order_index)
        ],
    }


@router.get("/journey")
def preview_journey(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # `user` is deliberately resolved even though it is not included in the
    # payload: the endpoint is supervisor-only and must never be public.
    _ = user.id
    items = (
        db.query(ContentItem)
        .options(
            joinedload(ContentItem.skill),
            joinedload(ContentItem.steps).joinedload(ContentStep.options),
            joinedload(ContentItem.steps).joinedload(ContentStep.assets),
            joinedload(ContentItem.assets),
        )
        .all()
    )

    sections = []
    for key, label, kind, level_id in SECTION_SPECS:
        section_items = [
            item
            for item in items
            if item.kind == kind and (level_id is None or int(item.level_id) == level_id)
        ]
        section_items.sort(key=lambda item: (int(item.order_index), int(item.id)))
        payload_items = [_item_payload(item) for item in section_items]
        sections.append({
            "key": key,
            "label": label,
            "kind": kind,
            "level_id": level_id,
            "item_count": len(payload_items),
            "round_count": sum(len(item["steps"]) for item in payload_items),
            "items": payload_items,
        })

    return {
        "version": "HIMMA-SUPERVISOR-CONTENT-PREVIEW-1.0",
        "read_only": True,
        "adaptive_logic": False,
        "results_persisted": False,
        "item_count": sum(section["item_count"] for section in sections),
        "round_count": sum(section["round_count"] for section in sections),
        "sections": sections,
    }
