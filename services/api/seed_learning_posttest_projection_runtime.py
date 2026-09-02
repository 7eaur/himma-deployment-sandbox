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
LISTEN_WITH_VISIBLE_STIMULUS = {"L1-CORE-06"}

# These level-one tasks explicitly require one visible letter/word/printed item.
# Their legacy prompt_text often serializes that item together with choices, so
# never pass the raw prompt through to the student-facing stimulus box.
L1_SINGLE_VISIBLE_STIMULUS = {
    "L1-CORE-01",
    "L1-CORE-03",
    "L1-CORE-07",
    "L1-REIN-01",
    "L1-REIN-07",
    "L1-REIN-09",
}

# Hints guide the learner without directly printing one of the answer choices.
# These overrides replace legacy hints that literally contained the correct
# classification/direction option and therefore leaked the answer after error.
SAFE_HINT_OVERRIDES = {
    "L1-CORE-07": "لاحظ حجم العنصر وعدد الرموز والمسافات بين أجزائه، ثم اختر التصنيف المناسب.",
    "L1-CORE-09": "تذكّر جهة البداية في السطر العربي، ثم فكّر في اتجاه متابعة القراءة.",
    "L1-REIN-11": "تذكّر جهة بداية السطر العربي، ثم اختر الاتجاه المناسب دون استعجال.",
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
    """Extract only the one student-visible target, never its serialized choices."""
    value = _strip_serialized_choices(text)
    quoted = re.search(r"«([^»]+)»", value)
    if quoted:
        return quoted.group(1).strip()

    # Source rounds use forms such as `ب: ب/ت`, `ب ← حرف`, `ب → بـ / تـ`,
    # or `ب = حرف`.
    for separator in ("←", "→", "=", ":"):
        if separator in value:
            value = value.split(separator, 1)[0].strip()
            break

    # A legacy prompt can still contain slash-separated choices without a colon.
    if "/" in value:
        value = value.split("/", 1)[0].strip()
    # Preserve meaningful sentence punctuation. Only remove wrapper punctuation
    # that can be introduced by legacy prompt serialization.
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

    if key == "L1-CORE-06":
        # Student Experience v2 currently projects a heard sound against one
        # displayed word. Keep the display box to that word only; source-version
        # reconciliation is audited separately from presentation correctness.
        value = _strip_serialized_choices(text)
        if ":" in value:
            value = value.split(":", 1)[1].strip()
        return value.strip(" ،؛«»")

    return _strip_serialized_choices(text)


def _learning_round(item: ContentItem, step, total: int) -> dict[str, Any]:
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
