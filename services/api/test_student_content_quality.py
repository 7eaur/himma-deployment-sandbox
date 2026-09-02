"""Student-facing copy quality gates beyond structural schema validation."""
from __future__ import annotations

import re
import unicodedata

import seed_all
from content_runtime import canonical_id, presentation_data
from db.database import SessionLocal
from db.models import ContentItem

SERIALIZED = ("الخيارات:", "الإجابة الصحيحة:", "طريقة الإجابة:", "criterion:", "options:")


def _plain(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def test_student_visible_copy_has_no_serialized_source_fragments_or_empty_choices():
    result = seed_all.run_seed_all()
    assert result["total_items"] == 125
    db = SessionLocal()
    errors: list[str] = []
    try:
        for item in db.query(ContentItem).all():
            canonical = canonical_id(item)
            for step in item.steps:
                presentation = presentation_data(item, step)
                visible_fields = []
                if item.kind in {"core_activity", "reinforcement_activity"}:
                    visible_fields = [
                        str(presentation.get("question_text") or ""),
                        str(presentation.get("instruction_text") or ""),
                        str(presentation.get("stimulus_text") or ""),
                        str(presentation.get("encouragement") or ""),
                        str(presentation.get("hint") or ""),
                    ]
                else:
                    stimulus = presentation.get("stimulus") or {}
                    visible_fields = [
                        str(presentation.get("question_text") or ""),
                        str(presentation.get("instruction_text") or ""),
                        str(stimulus.get("text") or ""),
                        str(presentation.get("encouragement") or ""),
                    ]
                joined = " | ".join(visible_fields)
                leaked = [marker for marker in SERIALIZED if marker in joined]
                if leaked:
                    errors.append(f"{canonical}/R{step.order_index}: serialized markers {leaked}")
                for option in step.options:
                    if not _plain(option.text):
                        errors.append(f"{canonical}/R{step.order_index}: empty option id={option.id}")
        assert not errors, "\n".join(errors)
    finally:
        db.close()


def test_learning_hints_do_not_directly_print_a_nontrivial_correct_choice():
    """A retry hint may guide the skill, but must not simply state the answer."""
    result = seed_all.run_seed_all()
    assert result["learning_experience_items"] == 65
    db = SessionLocal()
    leaks: list[str] = []
    try:
        for item in db.query(ContentItem).filter(ContentItem.kind.in_(["core_activity", "reinforcement_activity"])).all():
            canonical = canonical_id(item)
            for step in item.steps:
                presentation = presentation_data(item, step)
                hint = _plain(str(presentation.get("hint") or ""))
                if not hint:
                    continue
                correct_texts = [_plain(option.text) for option in step.options if option.is_correct]
                for answer in correct_texts:
                    # Single letters/syllables naturally occur inside Arabic prose; only
                    # flag direct answer leakage for meaningful words/phrases/symbol labels.
                    compact = re.sub(r"\s+", "", answer)
                    if len(compact) < 4:
                        continue
                    if answer and answer in hint:
                        leaks.append(f"{canonical}/R{step.order_index}: hint={hint!r} contains answer={answer!r}")
        assert not leaks, "Direct answer leakage in learning hints:\n" + "\n".join(leaks)
    finally:
        db.close()
