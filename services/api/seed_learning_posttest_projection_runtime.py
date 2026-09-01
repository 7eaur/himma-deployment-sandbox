"""Runtime adapter for the 2026-09-01 learning/posttest projection.

The immutable content model stores display instructions in template_data rather
than ContentStep columns. Patch the projection helper to read the canonical
runtime instruction API without altering the database schema.
"""
from __future__ import annotations

from typing import Any

import seed_learning_posttest_experience_2026_09_01 as base
from content_runtime import instruction_text as runtime_instruction_text
from db.models import ContentItem


def _learning_round(item: ContentItem, step, total: int) -> dict[str, Any]:
    key = base.canonical(item)
    override = base.ITEM_OVERRIDES.get(key, {})
    interaction = str((item.template_data or {}).get("canonical_interaction_type") or item.interaction_type)
    raw_instruction = str(runtime_instruction_text(item, step) or "")
    raw_prompt = str(step.prompt_text or "")
    question = override.get("question") or base.generic_question(interaction, raw_instruction, raw_prompt)
    instruction = override.get("instruction") or base.generic_instruction(interaction, question)
    title = str((item.template_data or {}).get("title") or item.stable_key)
    return {
        "round_number": int(step.order_index),
        "round_total": total,
        "skill": override.get("skill") or title,
        "encouragement": base.encouragement(int(step.order_index), total),
        "hint": override.get("hint") or base.generic_hint(interaction, question),
        "question_text": question,
        "instruction_text": instruction,
    }


base.learning_round = _learning_round
LEARNING_VERSION = base.LEARNING_VERSION
POSTTEST_VERSION = base.POSTTEST_VERSION
run_seed = base.run_seed
