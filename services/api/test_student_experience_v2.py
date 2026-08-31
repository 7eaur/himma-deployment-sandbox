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


def test_path_tasks_are_replaced_without_changing_item_counts():
    seed_all.run_seed_all()
    db = SessionLocal()
    try:
        for canonical in ("L1-CORE-09", "L1-REIN-11"):
            item = _item(db, canonical)
            assert (item.template_data or {}).get("canonical_interaction_type") == "choose_one"
            assert "path" not in str((item.template_data or {}).get("canonical_interaction_type"))
            assert len(item.steps) == 5
            for step in item.steps:
                options = sorted(step.options, key=lambda option: option.order_index)
                assert len(options) == 2
                assert sum(1 for option in options if option.is_correct) == 1
        assert "من أين نبدأ القراءة" in (_item(db, "L1-CORE-09").template_data or {}).get("title", "")
        assert "يمين أم يسار" in (_item(db, "L1-REIN-11").template_data or {}).get("title", "")
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
