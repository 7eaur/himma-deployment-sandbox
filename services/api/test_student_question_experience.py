"""Regression gates for the student question-experience maintenance slice.

These tests protect the approved academic semantics while making sure the
student-facing runtime never falls back to vague copy or empty choice tasks.
"""

import seed_all
from content_runtime import canonical_id, canonical_interaction, instruction_text, presentation_data
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


def _learning_rounds(item: ContentItem) -> list[dict]:
    data = item.template_data or {}
    experience = data.get("learning_experience") or {}
    return list(experience.get("rounds") or [])


def _display_copy(item: ContentItem) -> str:
    step = item.steps[0]
    presentation = presentation_data(item, step)
    return " ".join([
        str(presentation.get("question_text") or ""),
        str(presentation.get("instruction_text") or ""),
    ]).strip()


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
        copy = _display_copy(image_onset)
        assert "الصورة" in copy
        assert "يبدأ اسمها" in copy

        initial_sound = _by_canonical(db, "PRE-Q06")
        copy = _display_copy(initial_sound)
        assert "تبدأ به" in copy or "أول صوت" in copy

        final_sound = _by_canonical(db, "PRE-Q07")
        copy = _display_copy(final_sound)
        assert "تنتهي به" in copy or "آخر صوت" in copy

        # Latest approved L1-CORE-06 compares the onsets of two heard words.
        # No word from the pair is exposed in the visible stimulus box.
        onset = _by_canonical(db, "L1-CORE-06")
        copy = _display_copy(onset)
        assert "الكلمتين" in copy
        assert "أول صوت" in copy or "بدا" in copy
        assert canonical_interaction(onset) == "listen_choose_one"
        option_texts = {
            option.text
            for step in onset.steps
            for option in step.options
        }
        assert {"الصوت نفسه", "صوتان مختلفان"} <= option_texts

        pair = (onset.template_data or {}).get("onset_pair_compare") or {}
        assert [round_data["audio_words"] for round_data in pair.get("rounds", [])] == [
            ["موز", "ماء"],
            ["باب", "بطة"],
            ["قلم", "كرة"],
            ["سمك", "شمس"],
            ["نور", "نخلة"],
        ]
    finally:
        db.close()


def test_level_one_visible_stimulus_never_serializes_its_choices():
    """The display box contains only the approved target; listening pairs stay audio-only."""
    _seed()
    db = SessionLocal()
    try:
        expected = {
            "L1-CORE-01": ["ب", "ج", "س", "ق", "د"],
            "L1-CORE-03": ["ب", "م", "س", "ك", "ل"],
            "L1-CORE-06": ["", "", "", "", ""],
            "L1-CORE-07": ["ب", "كِتَاب", "ذَهَبَ سَالِمٌ.", "م", "شَجَرَة"],
        }
        for canonical, wanted in expected.items():
            item = _by_canonical(db, canonical)
            rounds = _learning_rounds(item)
            actual = [str(round_data.get("stimulus_text") or "").strip() for round_data in rounds]
            assert actual == wanted, (canonical, actual)
            for stimulus in actual:
                assert "الخيارات" not in stimulus
                assert "/" not in stimulus
                assert "؛" not in stimulus
    finally:
        db.close()


def test_level_one_direction_content_is_fully_replaced_by_auditory_comprehension():
    _seed()
    db = SessionLocal()
    try:
        core = _by_canonical(db, "L1-CORE-09")
        rein = _by_canonical(db, "L1-REIN-11")
        for item, expected_title in [
            (core, "استمع إلى القصة ثم أجب"),
            (rein, "استمع واختر الإجابة"),
        ]:
            data = item.template_data or {}
            story = data.get("auditory_story") or {}
            assert story.get("student_visible_story_text") is False
            assert story.get("skill") == "الفهم السمعي المباشر"
            assert data.get("canonical_interaction_type") == "listen_choose_one"
            assert expected_title in str(data.get("title") or "")
            rounds = _learning_rounds(item)
            assert len(rounds) == 5
            assert all(not str(round_data.get("stimulus_text") or "").strip() for round_data in rounds)
            visible = " ".join(
                str(round_data.get("question_text") or "") + " " + str(round_data.get("instruction_text") or "")
                for round_data in rounds
            )
            assert "اتجاه القراءة" not in visible
            assert "يمين أم يسار" not in visible
    finally:
        db.close()
