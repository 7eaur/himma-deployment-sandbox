"""Idempotent migration for the user-approved Student Experience v2 content contract.

This migration is intentionally separate from the immutable 105-item client
baseline. It makes the newly approved student-facing content authoritative in
runtime while preserving canonical IDs, skill assignments, item order and the
125-item journey contract.

Explicit changes:
- L1-CORE-06 becomes letter-sound versus first letter of a displayed word.
- L1-CORE-09 replaces the path-tracing task with Arabic reading-direction work.
- L1-REIN-11 replaces the path reinforcement with a simpler direction task.
- POST-Q14 is made semantically coherent: palm-tree image -> نَخْلَة.
"""
from __future__ import annotations

from typing import Iterable

from db.database import SessionLocal
from db.models import ContentAssetLink, ContentItem, ContentOption

VERSION = "HIMMA-STUDENT-EXPERIENCE-2.0"


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
    # Do not remove through the relationship collection: ContentOption.step_id is
    # NOT NULL, so relationship disassociation would emit step_id=NULL. Delete
    # retired projection rows explicitly instead.
    for extra in options[2:]:
        db.delete(extra)


def _set_prompt_audio(db, step, asset_id: str, semantic_text: str) -> None:
    prompt_assets = [
        asset for asset in step.assets
        if asset.asset_type == "audio" and asset.usage_context == "prompt"
    ]
    if prompt_assets:
        prompt_assets[0].manifest_asset_id = asset_id
        for extra in prompt_assets[1:]:
            db.delete(extra)
    else:
        db.add(ContentAssetLink(
            step_id=step.id,
            manifest_asset_id=asset_id,
            asset_type="audio",
            usage_context="prompt",
        ))


def _replace_onset_compare(db) -> None:
    item = _find_item(db, "L1-CORE-06")
    _mark(item, title="النشاط الأساسي 6: بداية الكلمة — متشابهان أم مختلفان؟", interaction="listen_choose_one")
    rounds = [
        ("م", "LET-01", "مَوْزَة", "متشابهان"),
        ("ب", "LET-02", "قَلَم", "مختلفان"),
        ("ق", "LET-04", "قَمَر", "متشابهان"),
        ("س", "LET-03", "شَمْس", "مختلفان"),
        ("ن", "LET-06", "نَخْلَة", "متشابهان"),
    ]
    steps = sorted(item.steps, key=lambda step: step.order_index)
    if len(steps) != len(rounds):
        raise RuntimeError("L1-CORE-06 must have five rounds")
    for step, (sound, audio_id, word, answer) in zip(steps, rounds, strict=True):
        _set_two_choice_step(
            db,
            step,
            prompt=f"الكلمة المعروضة: {word}",
            first="متشابهان",
            second="مختلفان",
            answer=answer,
        )
        _set_prompt_audio(db, step, audio_id, sound)


def _replace_direction_item(db, canonical: str, *, title: str, rounds: Iterable[tuple[str, str, str, str]]) -> None:
    item = _find_item(db, canonical)
    _mark(item, title=title, interaction="choose_one")
    steps = sorted(item.steps, key=lambda step: step.order_index)
    round_list = list(rounds)
    if len(steps) != len(round_list):
        raise RuntimeError(f"{canonical} round count mismatch")
    for step, (prompt, first, second, answer) in zip(steps, round_list, strict=True):
        _set_two_choice_step(db, step, prompt=prompt, first=first, second=second, answer=answer)
        # The replacement is intentionally non-audio/non-path. Delete obsolete
        # links explicitly so no NOT NULL foreign key is nulled by disassociation.
        for asset in list(step.assets):
            if asset.asset_type == "audio" or asset.usage_context in {"path", "prompt"}:
                db.delete(asset)


def _replace_direction_tasks(db) -> None:
    _replace_direction_item(
        db,
        "L1-CORE-09",
        title="النشاط الأساسي 9: من أين نبدأ القراءة؟",
        rounds=[
            ("أين نبدأ قراءة السطر العربي؟", "من اليمين", "من اليسار", "من اليمين"),
            ("أي سهم يوضح اتجاه القراءة في العربية؟", "←", "→", "←"),
            ("إذا كانت «كِتَاب» على يمين «قَلَم»، فأي كلمة نقرأ أولًا؟", "كِتَاب", "قَلَم", "كِتَاب"),
            ("أين تكون بداية السطر العربي؟", "الطرف الأيمن", "الطرف الأيسر", "الطرف الأيمن"),
            ("بعد أن نبدأ من اليمين، إلى أين نتابع القراءة؟", "نحو اليسار", "نحو اليمين", "نحو اليسار"),
        ],
    )
    _replace_direction_item(
        db,
        "L1-REIN-11",
        title="يمين أم يسار؟",
        rounds=[
            ("اختر جهة بداية القراءة بالعربية.", "اليمين", "اليسار", "اليمين"),
            ("اختر سهم اتجاه القراءة الصحيح.", "←", "→", "←"),
            ("أين نضع نظرنا أولًا عند قراءة سطر عربي؟", "في اليمين", "في اليسار", "في اليمين"),
            ("بعد الكلمة الأولى نتابع القراءة في أي اتجاه؟", "نحو اليسار", "نحو اليمين", "نحو اليسار"),
            ("اختر الترتيب الصحيح: بداية السطر ثم المتابعة.", "يمين ثم يسار", "يسار ثم يمين", "يمين ثم يسار"),
        ],
    )


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
        _replace_direction_tasks(db)
        _repair_post_q14(db)
        _mark_all_items(db)
        db.commit()
        return 4
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print(f"Student Experience v2 migrations applied: {run_seed()}")
