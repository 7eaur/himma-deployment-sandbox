"""Regression coverage for the 2026-09-01 user-approved pretest contract."""

import seed_all
from db.database import SessionLocal
from db.models import ContentItem


VERSION = "HIMMA-PRETEST-2026-09-01"


def _item(db, canonical_id: str) -> ContentItem:
    for item in db.query(ContentItem).filter(ContentItem.kind == "pretest_question").all():
        if str((item.template_data or {}).get("canonical_id") or item.stable_key) == canonical_id:
            return item
    raise AssertionError(f"Missing pretest item: {canonical_id}")


def test_pretest_overlay_projects_all_30_questions_into_runtime():
    result = seed_all.run_seed_all()
    assert result["pretest_experience_items"] == 30

    db = SessionLocal()
    try:
        pretest = db.query(ContentItem).filter(ContentItem.kind == "pretest_question").all()
        assert len(pretest) == 30
        assert all((item.template_data or {}).get("pretest_experience_version") == VERSION for item in pretest)

        q1 = _item(db, "PRE-Q01")
        q1_data = q1.template_data["pretest_experience"]
        assert q1_data["question_text"] == "اضغط على الحرف التالي."
        assert q1_data["stimulus"] == {"kind": "text", "text": "ب"}
        assert q1.steps[0].prompt_text == "ب"
        assert [option.text for option in q1.steps[0].options] == ["ت", "ب", "ث", "ن"]
        assert [option.text for option in q1.steps[0].options if option.is_correct] == ["ب"]

        q3 = _item(db, "PRE-Q03")
        q3_data = q3.template_data["pretest_experience"]
        assert q3_data["stimulus"] == {"kind": "text", "text": "م"}
        assert q3.steps[0].prompt_text == "م"
        assert "مـ" not in q3.steps[0].prompt_text
        assert [option.text for option in q3.steps[0].options] == ["مـ", "سـ", "لـ", "بـ"]

        q4 = _item(db, "PRE-Q04")
        assert q4.interaction_type == "listen_choose_one"
        assert q4.template_data["canonical_interaction_type"] == "listen_choose_one"
        assert q4.steps[0].prompt_text == ""
        assert q4.template_data["pretest_experience"]["stimulus"]["audio_target"] == "س"

        q19 = _item(db, "PRE-Q19")
        assert q19.interaction_type == "read_aloud"
        assert q19.template_data["canonical_interaction_type"] == "read_aloud"
        assert q19.steps[0].expected_reading_text == "كَتَبَ"

        q24 = _item(db, "PRE-Q24")
        assert "فِي صَبَاحِ يَوْمِ الْجُمُعَةِ" in q24.steps[0].expected_reading_text
        assert "سَلَّةِ الْمُهْمَلَاتِ" in q24.steps[0].expected_reading_text

        q30 = _item(db, "PRE-Q30")
        q30_data = q30.template_data["pretest_experience"]
        assert q30_data["question_text"] == "ما معنى كلمة «قُرْبَ» في الجملة؟"
        assert q30.steps[0].prompt_text == "لعب الطفلان قرب شجرة"
        assert [option.text for option in q30.steps[0].options] == ["بجانب.", "بعيدًا عن.", "فوق."]
        assert [option.text for option in q30.steps[0].options if option.is_correct] == ["بجانب."]
    finally:
        db.close()
