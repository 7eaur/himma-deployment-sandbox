"""Regression gates for the deterministic structured learning projection."""
from pathlib import Path

import seed_all
from content_runtime import canonical_id
from db.database import SessionLocal
from db.models import ContentItem


def _by_key(db, key: str) -> ContentItem:
    for item in db.query(ContentItem).all():
        if canonical_id(item) == key:
            return item
    raise AssertionError(f"Missing seeded item {key}")


def _round(item: ContentItem, number: int) -> dict:
    experience = dict((item.template_data or {}).get("learning_experience") or {})
    assert experience.get("projection_contract") == "structured_db_runtime_v1"
    rounds = list(experience.get("rounds") or [])
    assert 1 <= number <= len(rounds)
    return dict(rounds[number - 1])


def test_active_projection_does_not_parse_legacy_prompt_text():
    source = Path(__file__).with_name("seed_learning_posttest_projection_runtime.py").read_text(encoding="utf-8")
    assert "import re" not in source
    assert "step.prompt_text" not in source
    assert "_extract_quoted" not in source
    assert "_single_visible_stimulus" not in source
    assert "_strip_serialized_choices" not in source
    assert "_clean_stimulus" not in source
    assert "structured_db_runtime_v1" in source


def test_structured_projection_keeps_answers_out_of_student_stimuli():
    result = seed_all.run_seed_all()
    assert result["learning_experience_items"] == 65

    db = SessionLocal()
    try:
        l1_print = _round(_by_key(db, "L1-CORE-07"), 1)
        assert l1_print["stimulus_text"] == "ب"
        assert "حرف" not in l1_print["stimulus_text"]

        missing_letter = _round(_by_key(db, "L2-REIN-01"), 1)
        assert missing_letter["stimulus_text"] == "_اب"
        assert "بَاب" not in missing_letter["stimulus_text"]
        assert missing_letter["question_text"] == "اختر الحرف الناقص لإكمال الكلمة."

        direct = _round(_by_key(db, "L3-CORE-07"), 1)
        assert direct["question_text"] == "أين دخل خالد؟"
        assert direct["stimulus_text"] == ""
        assert "المكتبة" not in direct["question_text"]

        inference = _round(_by_key(db, "L3-CORE-08"), 1)
        assert inference["question_text"] == "لماذا أحضر الأب الماء؟"
        assert "لأنهم سيقضون" not in inference["question_text"]
        assert inference["stimulus_text"] == ""

        vocabulary = _round(_by_key(db, "L3-CORE-09"), 1)
        assert vocabulary["stimulus_text"] == "هَادِئ"
        assert "قليل الضوضاء" not in vocabulary["stimulus_text"]
        assert vocabulary["question_text"] == "اختر معنى الكلمة."

        evidence = _round(_by_key(db, "L3-REIN-02"), 1)
        assert evidence["stimulus_text"] == "المطر"
        assert "حمل سالم مظلته" not in evidence["stimulus_text"]
        assert evidence["question_text"] == "اختر جملة الدليل المناسبة."

        title = _round(_by_key(db, "L3-REIN-05"), 1)
        assert title["stimulus_text"] == ""
        assert title["question_text"] == "اختر عنوان النص المناسب."
    finally:
        db.close()


def test_structured_addition_prompt_and_approved_onset_pair_are_preserved():
    seed_all.run_seed_all()
    db = SessionLocal()
    try:
        addition = _round(_by_key(db, "L3-REIN-09"), 1)
        assert addition["stimulus_text"].startswith("جَلَسَ خَالِدٌ قُرْبَ الْبَابِ.")
        assert "بجانب" not in addition["stimulus_text"]
        assert addition["question_text"] == "اختر معنى الكلمة من الجملة."

        onset = _round(_by_key(db, "L1-CORE-06"), 1)
        assert onset["question_text"] == "استمع إلى الكلمتين، ثم حدّد: هل تبدأان بالصوت نفسه أم بصوتين مختلفين؟"
        assert onset["instruction_text"] == "استمع إلى الكلمتين كاملتين، ثم قارن أول صوت في كل كلمة."
        assert onset["stimulus_text"] == ""
    finally:
        db.close()
