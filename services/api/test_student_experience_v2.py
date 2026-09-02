from __future__ import annotations

from db.database import SessionLocal
from db.models import ContentItem
import seed_all


def _item(db, canonical: str) -> ContentItem:
    for item in db.query(ContentItem).all():
        if str((item.template_data or {}).get("canonical_id") or item.stable_key) == canonical:
            return item
    raise AssertionError(f"missing {canonical}")


def test_student_experience_v2_is_authoritative_for_all_runtime_items():
    result = seed_all.run_seed_all()
    assert result["total_items"] == 125
    assert result["student_experience_v2_items"] == 125

    db = SessionLocal()
    try:
        items = db.query(ContentItem).all()
        assert len(items) == 125
        assert all(
            (item.template_data or {}).get("student_experience_version")
            == "HIMMA-STUDENT-EXPERIENCE-2.0"
            for item in items
        )
    finally:
        db.close()


def test_onset_comparison_is_sound_against_first_letter_not_two_words():
    seed_all.run_seed_all()
    db = SessionLocal()
    try:
        item = _item(db, "L1-CORE-06")
        assert (item.template_data or {}).get("canonical_interaction_type") == "listen_choose_one"
        assert "بداية الكلمة" in (item.template_data or {}).get("title", "")
        expected = [
            ("مَوْزَة", "LET-01", "متشابهان"),
            ("قَلَم", "LET-02", "مختلفان"),
            ("قَمَر", "LET-04", "متشابهان"),
            ("شَمْس", "LET-03", "مختلفان"),
            ("نَخْلَة", "LET-06", "متشابهان"),
        ]
        steps = sorted(item.steps, key=lambda step: step.order_index)
        assert len(steps) == 5
        for step, (word, audio_id, answer) in zip(steps, expected, strict=True):
            assert word in step.prompt_text
            options = sorted(step.options, key=lambda option: option.order_index)
            assert [option.text for option in options] == ["متشابهان", "مختلفان"]
            assert next(option.text for option in options if option.is_correct) == answer
            prompt_audio = [
                asset.manifest_asset_id
                for asset in step.assets
                if asset.asset_type == "audio" and asset.usage_context == "prompt"
            ]
            assert prompt_audio == [audio_id]
    finally:
        db.close()


def test_path_tasks_are_replaced_by_approved_auditory_comprehension():
    result = seed_all.run_seed_all()
    assert result["auditory_story_changes"] == 2
    assert result["auditory_runtime_changes"] == 2

    db = SessionLocal()
    try:
        expected = {
            "L1-CORE-09": {
                "title": "النشاط الأساسي 9: استمع إلى القصة ثم أجب",
                "story": "ذهبت ليان مع أبيها إلى المزرعة في الصباح. رأت أرنبًا أبيض قرب الشجرة، فأعطته جزرة. ثم ساعدت أباها في سقي النباتات. وقبل أن تعود إلى البيت، قطفت زهرة صفراء لأمها.",
                "first_question": "أين ذهبت ليان؟",
                "first_options": ["إلى المزرعة", "إلى المدرسة", "إلى السوق"],
            },
            "L1-REIN-11": {
                "title": "استمع واختر الإجابة",
                "story": "ذهب نادر مع أخته إلى الشاطئ. بنيا قلعة من الرمل، ثم جمعا أصدافًا جميلة. وبعد اللعب جلسا تحت المظلة وشربا الماء، ثم عادا إلى البيت.",
                "first_question": "أين ذهب نادر؟",
                "first_options": ["إلى الشاطئ", "إلى المزرعة", "إلى المدرسة"],
            },
        }
        for canonical, wanted in expected.items():
            item = _item(db, canonical)
            data = item.template_data or {}
            story = data.get("auditory_story") or {}
            assert data.get("canonical_interaction_type") == "listen_choose_one"
            assert data.get("title") == wanted["title"]
            assert story.get("skill") == "الفهم السمعي المباشر"
            assert story.get("story_text_internal") == wanted["story"]
            assert story.get("audio_asset_id") is None
            assert story.get("audio_status") == "pending_audio_asset"
            assert story.get("student_visible_story_text") is False
            assert len(item.steps) == 5
            assert len(story.get("rounds") or []) == 5
            assert story["rounds"][0]["question_text"] == wanted["first_question"]
            options = sorted(item.steps[0].options, key=lambda option: option.order_index)
            assert [option.text for option in options] == wanted["first_options"]
            assert sum(1 for option in options if option.is_correct) == 1
            assert all(not step.assets for step in item.steps)

            runtime = data.get("db_runtime") or {}
            assert len(runtime.get("rounds") or []) == 5
            for runtime_round in runtime["rounds"]:
                assert runtime_round.get("assets") == []
                gaps = runtime_round.get("media_gaps") or []
                assert len(gaps) == 1
                assert gaps[0]["asset_type"] == "audio"
                assert gaps[0]["status"] == "pending_audio_asset"

            learning = data.get("learning_experience") or {}
            assert len(learning.get("rounds") or []) == 5
            assert all((round_data.get("stimulus_text") or "") == "" for round_data in learning["rounds"])
            assert learning["rounds"][0]["question_text"] == wanted["first_question"]
    finally:
        db.close()


def test_post_q14_image_and_target_word_are_coherent():
    seed_all.run_seed_all()
    db = SessionLocal()
    try:
        item = _item(db, "POST-Q14")
        step = sorted(item.steps, key=lambda value: value.order_index)[0]
        assert "نَخْلَة" in step.prompt_text
        options = sorted(step.options, key=lambda option: option.order_index)
        assert [option.text for option in options[:4]] == ["ن", "خ", "ل", "ة"]
        assert all(option.is_correct for option in options[:4])
    finally:
        db.close()
