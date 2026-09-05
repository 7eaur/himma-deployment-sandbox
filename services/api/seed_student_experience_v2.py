"""Idempotent migration for the reconciled Student Experience v2 contract.

The immutable 105-item baseline remains untouched. This runtime overlay applies
only approved student-facing corrections while preserving canonical IDs, item
order and the 125-item journey contract.

Authoritative 2026-09-02/03 corrections:
- L1-CORE-06 compares the beginnings of two heard words.
- L1-CORE-09 and L1-REIN-11 are handled by the approved auditory-story overlay.
- POST-Q14 targets نَخْلَة.
"""
from __future__ import annotations

from db.database import SessionLocal
from db.models import ContentItem, ContentOption

VERSION = "HIMMA-STUDENT-EXPERIENCE-2.0"
PAIR_VERSION = "HIMMA-L1-ONSET-PAIR-2026-09-03"


def _find_item(db, canonical: str) -> ContentItem:
    direct = db.query(ContentItem).filter(ContentItem.stable_key == canonical).first()
    if direct is not None:
        return direct
    for item in db.query(ContentItem).all():
        if str((item.template_data or {}).get("canonical_id") or "") == canonical:
            return item
    raise RuntimeError(f"Student Experience v2 item not found: {canonical}")


def _mark(item: ContentItem, *, title: str | None = None, interaction: str | None = None) -> None:
    data = dict(item.template_data or {})
    data["student_experience_version"] = VERSION
    if title is not None:
        data["title"] = title
    if interaction is not None:
        data["canonical_interaction_type"] = interaction
    item.template_data = data


def _set_two_choice_step(db, step, *, prompt: str, first: str, second: str, answer: str) -> None:
    step.prompt_text = prompt
    options = sorted(step.options, key=lambda option: option.order_index)
    while len(options) < 2:
        option = ContentOption(step_id=step.id, text="", is_correct=False, order_index=len(options) + 1)
        db.add(option)
        options.append(option)
    options[0].text = first
    options[0].order_index = 1
    options[0].is_correct = first == answer
    options[1].text = second
    options[1].order_index = 2
    options[1].is_correct = second == answer
    for extra in options[2:]:
        db.delete(extra)


def _replace_onset_compare(db) -> None:
    item = _find_item(db, "L1-CORE-06")
    _mark(item, title="النشاط الأساسي 6: متشابهان أم مختلفان؟", interaction="listen_choose_one")
    rounds = [
        (["موز", "ماء"], "الصوت نفسه"),
        (["باب", "بطة"], "الصوت نفسه"),
        (["قلم", "كرة"], "صوتان مختلفان"),
        (["سمك", "شمس"], "صوتان مختلفان"),
        (["نور", "نخلة"], "الصوت نفسه"),
    ]
    steps = sorted(item.steps, key=lambda step: step.order_index)
    if len(steps) != len(rounds):
        raise RuntimeError("L1-CORE-06 must have five rounds")

    data = dict(item.template_data or {})
    data["onset_pair_version"] = PAIR_VERSION
    data["onset_pair_compare"] = {
        "version": PAIR_VERSION,
        "skill": "التمييز السمعي بين بدايات الكلمات",
        "student_question": "استمع إلى الكلمتين، ثم حدّد: هل تبدأان بالصوت نفسه أم بصوتين مختلفين؟",
        "instruction": "استمع إلى الكلمتين كاملتين، ثم قارن أول صوت في كل كلمة.",
        "student_visible_pair_text": False,
        "rounds": [
            {"audio_words": words, "answer": answer}
            for words, answer in rounds
        ],
        "media_note": "لا يُنشأ أو يُستبدل أي ملف صوتي آليًا؛ أصل «موز» يبقى فجوة M08 المعلنة حتى يصل التسجيل المعتمد.",
    }
    item.template_data = data

    for step, (words, answer) in zip(steps, rounds, strict=True):
        _set_two_choice_step(
            db,
            step,
            prompt="مقارنة كلمتين مسموعتين — النص غير معروض للطالب",
            first="الصوت نفسه",
            second="صوتان مختلفان",
            answer=answer,
        )
        for asset in list(step.assets):
            if asset.asset_type == "audio" and asset.usage_context == "prompt":
                db.delete(asset)


def _repair_post_q14(db) -> None:
    item = _find_item(db, "POST-Q14")
    _mark(item, interaction="build_word")
    steps = sorted(item.steps, key=lambda step: step.order_index)
    if len(steps) != 1:
        raise RuntimeError("POST-Q14 must have one step")
    step = steps[0]
    step.prompt_text = "انظر إلى صورة النخلة، ثم اضغط الحروف بالترتيب لتكوّن كلمة «نَخْلَة»."
    wanted = ["ن", "خ", "ل", "ة"]
    options = sorted(step.options, key=lambda option: option.order_index)
    while len(options) < len(wanted):
        option = ContentOption(step_id=step.id, text="", is_correct=False, order_index=len(options) + 1)
        db.add(option)
        options.append(option)
    for index, text in enumerate(wanted, start=1):
        options[index - 1].text = text
        options[index - 1].order_index = index
        options[index - 1].is_correct = True
    for extra in options[len(wanted):]:
        extra.is_correct = False


def _mark_all_items(db) -> None:
    for item in db.query(ContentItem).all():
        data = dict(item.template_data or {})
        data["student_experience_version"] = VERSION
        item.template_data = data


def run_seed() -> int:
    db = SessionLocal()
    try:
        _replace_onset_compare(db)
        _repair_post_q14(db)
        _mark_all_items(db)
        db.commit()
        return 2
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print(f"Student Experience v2 reconciled migrations applied: {run_seed()}")
