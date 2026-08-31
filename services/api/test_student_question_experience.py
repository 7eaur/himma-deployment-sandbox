"""Regression gates for the student question-experience maintenance slice.

These tests protect the approved academic semantics while making sure the
student-facing runtime never falls back to vague copy or empty choice tasks.
"""

import seed_all
from content_runtime import canonical_id, canonical_interaction, instruction_text
from db.database import SessionLocal
from db.models import ContentItem


CHOICE_INTERACTIONS = {
    "choose_one",
    "listen_choose_one",
    "choose_image",
    "listen_choose_image",
    "choose_many",
    "listen_choose_many",
}
FORBIDDEN_GENERIC_COPY = {
    "اختر الإجابة الصحيحة.",
    "استمع جيدًا، ثم اختر الإجابة الصحيحة.",
    "اختر الصورة الصحيحة.",
    "استمع جيدًا، ثم اختر الصورة الصحيحة.",
    "أكمل المهمة التالية.",
}


def _seed():
    result = seed_all.run_seed_all()
    assert result["total_items"] == 125
    assert result["reinforcement_items"] == 35


def _by_canonical(db, wanted: str) -> ContentItem:
    for item in db.query(ContentItem).all():
        if canonical_id(item) == wanted:
            return item
    raise AssertionError(f"Missing canonical item {wanted}")


def test_all_runtime_steps_have_child_clear_non_generic_instructions():
    _seed()
    db = SessionLocal()
    try:
        items = db.query(ContentItem).order_by(ContentItem.id).all()
        assert len(items) == 125
        for item in items:
            assert item.steps, canonical_id(item)
            for step in item.steps:
                copy = instruction_text(item, step).strip()
                assert copy, canonical_id(item)
                assert copy not in FORBIDDEN_GENERIC_COPY, (canonical_id(item), copy)
                assert "مهمة واحدة في كل مرة" not in copy
    finally:
        db.close()


def test_every_choice_task_has_real_options_in_every_round():
    _seed()
    db = SessionLocal()
    try:
        for item in db.query(ContentItem).all():
            if canonical_interaction(item) not in CHOICE_INTERACTIONS:
                continue
            for step in item.steps:
                assert len(step.options) >= 2, (
                    canonical_id(item),
                    step.order_index,
                    canonical_interaction(item),
                )
    finally:
        db.close()


def test_known_ambiguous_questions_are_explained_by_their_real_intent():
    _seed()
    db = SessionLocal()
    try:
        image_onset = _by_canonical(db, "PRE-Q05")
        assert "الصورة" in instruction_text(image_onset, image_onset.steps[0])
        assert "يبدأ اسمها" in instruction_text(image_onset, image_onset.steps[0])

        initial_sound = _by_canonical(db, "PRE-Q06")
        assert "بدايتها" in instruction_text(initial_sound, initial_sound.steps[0])

        final_sound = _by_canonical(db, "PRE-Q07")
        assert "آخرها" in instruction_text(final_sound, final_sound.steps[0])

        # Student Experience v2 explicitly defines L1-CORE-06 as a heard letter
        # sound compared with the first letter of a displayed word. Assert the
        # canonical task directly rather than guessing by historical title text.
        onset = _by_canonical(db, "L1-CORE-06")
        copy = instruction_text(onset, onset.steps[0])
        assert "أول حرف" in copy
        assert "متشابهان أم مختلفان" in copy
        assert canonical_interaction(onset) == "listen_choose_one"
    finally:
        db.close()
