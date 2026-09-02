"""Approved L1 auditory-comprehension replacement.

Replaces the retired reading-direction activity/reinforcement with the exact
client-delivery story content. Audio assets are intentionally pending; no fake
or substitute audio is created. The story text is stored internally in the DB
and must never be rendered as visible stimulus text to the student.
"""
from __future__ import annotations

from db.database import SessionLocal
from db.models import ContentAssetLink, ContentItem, ContentOption

VERSION = "HIMMA-L1-AUDITORY-COMPREHENSION-2026-09-02"

STORIES = {
    "L1-CORE-09": {
        "title": "النشاط الأساسي 9: استمع إلى القصة ثم أجب",
        "skill": "الفهم السمعي المباشر",
        "story_text_internal": "ذهبت ليان مع أبيها إلى المزرعة في الصباح. رأت أرنبًا أبيض قرب الشجرة، فأعطته جزرة. ثم ساعدت أباها في سقي النباتات. وقبل أن تعود إلى البيت، قطفت زهرة صفراء لأمها.",
        "audio_asset_id": None,
        "audio_status": "pending_audio_asset",
        "rounds": [
            {"question_text": "أين ذهبت ليان؟", "instruction_text": "استمع إلى القصة، ثم اختر الإجابة الصحيحة.", "options": ["إلى المزرعة", "إلى المدرسة", "إلى السوق"], "answer": "إلى المزرعة", "hint": "تذكّر المكان الذي ذهبت إليه ليان في بداية القصة."},
            {"question_text": "مع من ذهبت ليان؟", "instruction_text": "استمع مرة أخرى إذا احتجت، ثم اختر الإجابة.", "options": ["مع أبيها", "مع معلمتها", "مع صديقتها"], "answer": "مع أبيها", "hint": "تذكّر من رافق ليان إلى المزرعة."},
            {"question_text": "ماذا رأت ليان قرب الشجرة؟", "instruction_text": "اختر ما سمعته في القصة.", "options": ["أرنبًا أبيض", "قطة سوداء", "عصفورًا صغيرًا"], "answer": "أرنبًا أبيض", "hint": "استمع للجزء الذي يذكر ما رأته ليان قرب الشجرة."},
            {"question_text": "ماذا أعطت ليان للأرنب؟", "instruction_text": "استمع ثم اختر الإجابة الصحيحة.", "options": ["جزرة", "تفاحة", "قطعة خبز"], "answer": "جزرة", "hint": "تذكّر الطعام الذي قدمته ليان للأرنب."},
            {"question_text": "ماذا فعلت ليان قبل أن تعود إلى البيت؟", "instruction_text": "اختر الحدث الذي جاء في نهاية القصة.", "options": ["قطفت زهرة صفراء لأمها", "لعبت بالكرة", "ذهبت إلى المدرسة"], "answer": "قطفت زهرة صفراء لأمها", "hint": "استمع إلى نهاية القصة وتذكّر ما أخذته ليان لأمها."},
        ],
    },
    "L1-REIN-11": {
        "title": "استمع واختر الإجابة",
        "skill": "الفهم السمعي المباشر",
        "story_text_internal": "ذهب نادر مع أخته إلى الشاطئ. بنيا قلعة من الرمل، ثم جمعا أصدافًا جميلة. وبعد اللعب جلسا تحت المظلة وشربا الماء، ثم عادا إلى البيت.",
        "audio_asset_id": None,
        "audio_status": "pending_audio_asset",
        "rounds": [
            {"question_text": "أين ذهب نادر؟", "instruction_text": "استمع إلى القصة، ثم اختر الإجابة الصحيحة.", "options": ["إلى الشاطئ", "إلى المزرعة", "إلى المدرسة"], "answer": "إلى الشاطئ", "hint": "تذكّر المكان الذي ذهب إليه نادر في بداية القصة."},
            {"question_text": "مع من ذهب نادر؟", "instruction_text": "استمع مرة أخرى إذا احتجت، ثم اختر الإجابة.", "options": ["مع أخته", "مع معلمه", "مع جاره"], "answer": "مع أخته", "hint": "استمع لأول جملة وتذكّر من رافق نادر."},
            {"question_text": "ماذا بنى نادر وأخته؟", "instruction_text": "اختر ما سمعته في القصة.", "options": ["قلعة من الرمل", "بيتًا من الخشب", "سورًا من الحجارة"], "answer": "قلعة من الرمل", "hint": "تذكّر ماذا صنعا بالرمل."},
            {"question_text": "ماذا جمع نادر وأخته؟", "instruction_text": "استمع ثم اختر الإجابة الصحيحة.", "options": ["أصدافًا", "أوراقًا", "أقلامًا"], "answer": "أصدافًا", "hint": "استمع لما حدث بعد بناء القلعة."},
            {"question_text": "ماذا شرب نادر وأخته؟", "instruction_text": "اختر ما سمعته بعد اللعب.", "options": ["الماء", "الحليب", "العصير"], "answer": "الماء", "hint": "تذكّر ما شرباه بعد اللعب."},
        ],
    },
}


def _find_item(db, canonical: str) -> ContentItem:
    for item in db.query(ContentItem).all():
        if item.stable_key == canonical or str((item.template_data or {}).get("canonical_id") or "") == canonical:
            return item
    raise RuntimeError(f"Missing auditory replacement item: {canonical}")


def _set_options(db, step, values: list[str], answer: str) -> None:
    options = sorted(step.options, key=lambda option: option.order_index)
    while len(options) < len(values):
        option = ContentOption(step_id=step.id, text="", is_correct=False, order_index=len(options) + 1)
        db.add(option)
        options.append(option)
    for index, value in enumerate(values, start=1):
        option = options[index - 1]
        option.text = value
        option.order_index = index
        option.is_correct = value == answer
    for extra in options[len(values):]:
        db.delete(extra)


def run_seed() -> int:
    db = SessionLocal()
    changed = 0
    try:
        for canonical, spec in STORIES.items():
            item = _find_item(db, canonical)
            steps = sorted(item.steps, key=lambda step: step.order_index)
            if len(steps) != 5:
                raise RuntimeError(f"{canonical} must have exactly five rounds")

            data = dict(item.template_data or {})
            data["title"] = spec["title"]
            data["canonical_interaction_type"] = "listen_choose_one"
            data["auditory_story_version"] = VERSION
            data["auditory_story"] = {
                "version": VERSION,
                "skill": spec["skill"],
                "story_text_internal": spec["story_text_internal"],
                "audio_asset_id": None,
                "audio_status": "pending_audio_asset",
                "student_visible_story_text": False,
                "rounds": spec["rounds"],
            }
            item.template_data = data

            for step, round_spec in zip(steps, spec["rounds"], strict=True):
                # prompt_text is retained only as a harmless internal marker; the
                # student renderer consumes learning_experience from DB instead.
                step.prompt_text = "قصة صوتية — النص غير معروض للطالب"
                step.expected_reading_text = None
                _set_options(db, step, round_spec["options"], round_spec["answer"])
                for asset in list(step.assets):
                    # Remove every obsolete direction/path/prompt asset. The new
                    # audio will be linked only after the approved file arrives.
                    db.delete(asset)
            changed += 1
        db.commit()
        return changed
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def patch_db_runtime() -> int:
    """Patch the DB-only runtime snapshot after the generic import snapshot."""
    db = SessionLocal()
    changed = 0
    try:
        for canonical, spec in STORIES.items():
            item = _find_item(db, canonical)
            data = dict(item.template_data or {})
            runtime = dict(data.get("db_runtime") or {})
            story = dict(data.get("auditory_story") or {})
            if not runtime or not story:
                raise RuntimeError(f"{canonical} DB runtime/story data missing")
            runtime["source_item"] = {
                "canonical_id": canonical,
                "title": spec["title"],
                "interaction_type": "listen_choose_one",
                "skill_name": spec["skill"],
                "story_text_internal": spec["story_text_internal"],
                "audio_asset_id": None,
                "audio_status": "pending_audio_asset",
                "rounds": [dict(value, order_index=index) for index, value in enumerate(spec["rounds"], start=1)],
            }
            runtime["rounds"] = [
                {
                    "order_index": index,
                    "source": dict(round_spec, order_index=index),
                    "assets": [],
                    "media_gaps": [{
                        "asset_type": "audio",
                        "usage": "prompt",
                        "semantic_text": spec["story_text_internal"],
                        "status": "pending_audio_asset",
                        "reason": "approved auditory story content is ready; audio file will be linked when supplied",
                    }],
                }
                for index, round_spec in enumerate(spec["rounds"], start=1)
            ]
            data["db_runtime"] = runtime
            item.template_data = data
            changed += 1
        db.commit()
        return changed
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print({"content_changed": run_seed(), "runtime_changed": patch_db_runtime()})
