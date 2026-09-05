from __future__ import annotations

from content_runtime import step_assets
from db.database import SessionLocal
from db.models import ContentItem, Skill
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
        assert all((item.template_data or {}).get("student_experience_version") == "HIMMA-STUDENT-EXPERIENCE-2.0" for item in items)
    finally:
        db.close()


def test_onset_comparison_uses_approved_two_word_auditory_contract():
    seed_all.run_seed_all()
    db = SessionLocal()
    try:
        item = _item(db, "L1-CORE-06")
        data = item.template_data or {}
        pair = data.get("onset_pair_compare") or {}
        assert data.get("canonical_interaction_type") == "listen_choose_one"
        assert data.get("title") == "النشاط الأساسي 6: متشابهان أم مختلفان؟"
        assert pair.get("student_visible_pair_text") is False
        assert pair.get("skill") == "التمييز السمعي بين بدايات الكلمات"
        expected = [
            (["موز", "ماء"], "الصوت نفسه"),
            (["باب", "بطة"], "الصوت نفسه"),
            (["قلم", "كرة"], "صوتان مختلفان"),
            (["سمك", "شمس"], "صوتان مختلفان"),
            (["نور", "نخلة"], "الصوت نفسه"),
        ]
        assert [(row["audio_words"], row["answer"]) for row in pair.get("rounds", [])] == expected
        steps = sorted(item.steps, key=lambda step: step.order_index)
        assert len(steps) == 5
        for step, (audio_words, answer) in zip(steps, expected, strict=True):
            assert step.prompt_text == "مقارنة كلمتين مسموعتين — النص غير معروض للطالب"
            options = sorted(step.options, key=lambda option: option.order_index)
            assert [option.text for option in options] == ["الصوت نفسه", "صوتان مختلفان"]
            assert next(option.text for option in options if option.is_correct) == answer
            audio_assets = [
                asset
                for asset in step_assets(item, step)
                if asset["asset_type"] == "audio" and asset["usage"] == "prompt"
            ]
            assert [asset["semantic_text"] for asset in audio_assets] == audio_words
        learning = data.get("learning_experience") or {}
        assert len(learning.get("rounds") or []) == 5
        assert all((row.get("stimulus_text") or "") == "" for row in learning["rounds"])
    finally:
        db.close()


def test_path_tasks_are_replaced_by_versioned_auditory_source_without_runtime_patch():
    result = seed_all.run_seed_all()
    assert result["auditory_story_changes"] == 2
    assert result["auditory_source_items"] == 2
    assert "auditory_runtime_changes" not in result

    db = SessionLocal()
    try:
        auditory_skill = db.query(Skill).filter(
            Skill.level_id == 1,
            Skill.canonical_skill_id == "auditory_literal_comprehension",
        ).one()
        assert auditory_skill.name == "الفهم السمعي المباشر"
        assert db.query(Skill).filter(Skill.canonical_skill_id == "visual_motor_direction").count() == 0

        expected = {
            "L1-CORE-09": {
                "title": "النشاط الأساسي 9: استمع إلى القصة ثم أجب",
                "audio_asset_id": "INS-01",
                "story": "ذهبت ليان مع أبيها إلى المزرعة في الصباح. رأت أرنبًا أبيض قرب الشجرة، فأعطته جزرة. ثم ساعدت أباها في سقي النباتات. وقبل أن تعود إلى البيت، قطفت زهرة صفراء لأمها.",
                "first_question": "أين ذهبت ليان؟",
                "first_options": ["إلى المزرعة", "إلى المدرسة", "إلى السوق"],
            },
            "L1-REIN-11": {
                "title": "استمع واختر الإجابة",
                "audio_asset_id": "INS-02",
                "story": "ذهب نادر مع أخته إلى الشاطئ. بنيا قلعة من الرمل، ثم جمعا أصدافًا جميلة. وبعد اللعب جلسا تحت المظلة وشربا الماء، ثم عادا إلى البيت.",
                "first_question": "أين ذهب نادر؟",
                "first_options": ["إلى الشاطئ", "إلى المزرعة", "إلى المدرسة"],
            },
        }
        for canonical, wanted in expected.items():
            item = _item(db, canonical)
            data = item.template_data or {}
            story = data.get("auditory_story") or {}
            assert item.skill_id == auditory_skill.id
            assert item.skill.canonical_skill_id == "auditory_literal_comprehension"
            assert item.skill.name == "الفهم السمعي المباشر"
            assert data.get("canonical_interaction_type") == "listen_choose_one"
            assert data.get("title") == wanted["title"]
            assert story.get("skill") == "الفهم السمعي المباشر"
            assert story.get("story_text_internal") == wanted["story"]
            assert story.get("audio_asset_id") == wanted["audio_asset_id"]
            assert story.get("audio_status") == "approved"
            assert story.get("student_visible_story_text") is False
            assert len(item.steps) == 5
            assert len(story.get("rounds") or []) == 5
            assert story["rounds"][0]["question_text"] == wanted["first_question"]
            options = sorted(item.steps[0].options, key=lambda option: option.order_index)
            assert [option.text for option in options] == wanted["first_options"]
            assert sum(1 for option in options if option.is_correct) == 1
            for step in item.steps:
                assets = step_assets(item, step)
                assert len(assets) == 1
                assert assets[0]["asset_id"] == wanted["audio_asset_id"]

            runtime = data.get("db_runtime") or {}
            assert runtime.get("source_item", {}).get("story_text_internal") == wanted["story"]
            assert runtime.get("source_item", {}).get("student_visible_story_text") is False
            assert len(runtime.get("rounds") or []) == 5
            for runtime_round in runtime["rounds"]:
                assert runtime_round.get("media_gaps") in (None, [])
                assets = runtime_round.get("assets") or []
                assert len(assets) == 1
                assert assets[0]["asset_id"] == wanted["audio_asset_id"]
                assert assets[0]["asset_type"] == "audio"
                assert assets[0]["semantic_text"] == wanted["story"]

            learning = data.get("learning_experience") or {}
            assert len(learning.get("rounds") or []) == 5
            assert all((round_data.get("stimulus_text") or "") == "" for round_data in learning["rounds"])
            assert learning["rounds"][0]["question_text"] == wanted["first_question"]

        retired = [
            str((item.template_data or {}).get("canonical_id") or item.stable_key)
            for item in db.query(ContentItem).all()
            if (item.template_data or {}).get("canonical_interaction_type") == "path_sequence"
        ]
        assert retired == []
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
