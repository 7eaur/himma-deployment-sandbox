"""Runtime adapter for the 2026-09-01 learning/posttest projection.

The immutable academic catalog stays untouched. This adapter stores a clean,
student-facing presentation contract in template_data so the UI never has to
show legacy prompt strings that also contain serialized choices.
"""
from __future__ import annotations

import re
from typing import Any

import seed_learning_posttest_experience_2026_09_01 as base
from content_runtime import instruction_text as runtime_instruction_text
from db.models import ContentItem

LEARNING_VERSION = "HIMMA-LEARNING-2026-09-01-R2"
POSTTEST_VERSION = base.POSTTEST_VERSION
LISTEN = {"listen_choose_one", "listen_choose_image", "listen_choose_many"}
NO_TEXT = {"read_aloud", "timed_read_aloud", "memory_sequence", "sequence", "build_word", "choose_image", "choose_many", "listen_choose_image", "listen_choose_many"}
LISTEN_WITH_VISIBLE_STIMULUS: set[str] = set()

L1_SINGLE_VISIBLE_STIMULUS = {
    "L1-CORE-01",
    "L1-CORE-03",
    "L1-CORE-07",
    "L1-REIN-01",
    "L1-REIN-07",
    "L1-REIN-09",
}

SAFE_HINT_OVERRIDES = {
    "L1-CORE-07": "لاحظ حجم العنصر وعدد الرموز والمسافات بين أجزائه، ثم اختر التصنيف المناسب.",
}


def _strip_serialized_choices(text: str) -> str:
    value = text.strip().replace("التعليمات:", "").strip()
    for marker in ("الخيارات:", "الصور:"):
        if marker in value:
            value = value.split(marker, 1)[0].strip()
    if "؛" in value:
        value = value.split("؛", 1)[0].strip()
    return value


def _single_visible_stimulus(text: str) -> str:
    value = _strip_serialized_choices(text)
    quoted = re.search(r"«([^»]+)»", value)
    if quoted:
        return quoted.group(1).strip()
    for separator in ("←", "→", "=", ":"):
        if separator in value:
            value = value.split(separator, 1)[0].strip()
            break
    if "/" in value:
        value = value.split("/", 1)[0].strip()
    return value.strip(" ،؛«»")


def _clean_stimulus(item: ContentItem, step, interaction: str) -> str:
    key = base.canonical(item)
    if interaction in NO_TEXT:
        return ""
    if interaction in LISTEN and key not in LISTEN_WITH_VISIBLE_STIMULUS:
        return ""
    text = str(step.prompt_text or "").strip()
    if not text:
        return ""
    if key in L1_SINGLE_VISIBLE_STIMULUS:
        return _single_visible_stimulus(text)
    return _strip_serialized_choices(text)


def _onset_pair_round(item: ContentItem, step, total: int) -> dict[str, Any] | None:
    pair = dict((item.template_data or {}).get("onset_pair_compare") or {})
    if not pair:
        return None
    rounds = list(pair.get("rounds") or [])
    index = int(step.order_index) - 1
    if index < 0 or index >= len(rounds):
        raise RuntimeError(f"{base.canonical(item)} onset pair round mismatch")
    return {
        "round_number": int(step.order_index),
        "round_total": total,
        "skill": str(pair.get("skill") or "التمييز السمعي بين بدايات الكلمات"),
        "encouragement": base.encouragement(int(step.order_index), total),
        "hint": "ركّز على بداية الكلمة الأولى ثم بداية الكلمة الثانية.",
        "question_text": str(pair.get("student_question") or "استمع إلى الكلمتين، ثم قارن بدايتهما."),
        "instruction_text": str(pair.get("instruction") or "استمع إلى الكلمتين كاملتين، ثم قارن أول صوت في كل كلمة."),
        "stimulus_text": "",
    }


def _auditory_story_round(item: ContentItem, step, total: int) -> dict[str, Any] | None:
    story = dict((item.template_data or {}).get("auditory_story") or {})
    if not story:
        return None
    rounds = list(story.get("rounds") or [])
    index = int(step.order_index) - 1
    if index < 0 or index >= len(rounds):
        raise RuntimeError(f"{base.canonical(item)} auditory story round mismatch")
    round_data = dict(rounds[index])
    return {
        "round_number": int(step.order_index),
        "round_total": total,
        "skill": str(story.get("skill") or "الفهم السمعي المباشر"),
        "encouragement": base.encouragement(int(step.order_index), total),
        "hint": str(round_data.get("hint") or ""),
        "question_text": str(round_data.get("question_text") or ""),
        "instruction_text": str(round_data.get("instruction_text") or ""),
        "stimulus_text": "",
    }


def _learning_round(item: ContentItem, step, total: int) -> dict[str, Any]:
    onset_pair = _onset_pair_round(item, step, total)
    if onset_pair is not None:
        return onset_pair
    auditory = _auditory_story_round(item, step, total)
    if auditory is not None:
        return auditory

    key = base.canonical(item)
    override = base.ITEM_OVERRIDES.get(key, {})
    interaction = str((item.template_data or {}).get("canonical_interaction_type") or item.interaction_type)
    raw_instruction = str(runtime_instruction_text(item, step) or "")
    raw_prompt = str(step.prompt_text or "")
    question = override.get("question") or base.generic_question(interaction, raw_instruction, raw_prompt)
    instruction = override.get("instruction") or base.generic_instruction(interaction, question)
    title = str((item.template_data or {}).get("title") or item.stable_key)
    hint = SAFE_HINT_OVERRIDES.get(key) or override.get("hint") or base.generic_hint(interaction, question)
    return {
        "round_number": int(step.order_index),
        "round_total": total,
        "skill": override.get("skill") or title,
        "encouragement": base.encouragement(int(step.order_index), total),
        "hint": hint,
        "question_text": question,
        "instruction_text": instruction,
        "stimulus_text": _clean_stimulus(item, step, interaction),
    }


def _apply_learning_r2(db) -> int:
    items = db.query(ContentItem).filter(ContentItem.kind.in_(["core_activity", "reinforcement_activity"])).all()
    if len(items) != 65:
        raise RuntimeError(f"Expected 65 learning items, got {len(items)}")
    changed = 0
    for item in items:
        steps = sorted(item.steps, key=lambda step: step.order_index)
        if not steps:
            raise RuntimeError(f"{base.canonical(item)} has no rounds")
        data = dict(item.template_data or {})
        projected = dict(data)
        projected["learning_experience_version"] = LEARNING_VERSION
        projected["learning_experience"] = {
            "version": LEARNING_VERSION,
            "rounds": [_learning_round(item, step, len(steps)) for step in steps],
        }
        if projected != data:
            item.template_data = projected
            changed += 1
    return changed


base.learning_round = _learning_round
base.apply_learning = _apply_learning_r2
base.LEARNING_VERSION = LEARNING_VERSION
run_seed = base.run_seed
