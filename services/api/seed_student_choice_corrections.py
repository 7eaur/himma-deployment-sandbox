"""Idempotent maintenance corrections for approved choice presentation.

These corrections repair import/runtime presentation gaps without rewriting the
immutable approved catalog. They keep each canonical item, correct answer,
scoring rule, skill, and activity order unchanged.

Most distractors below are copied verbatim from the client-approved source.
L3-REIN-01 is the one documented exception: the source explicitly requires the
same sentence to be shown in three segmentations but lists only the correct
segmentation. Its two distractors are therefore presentation-only boundary
variants generated from the exact same approved words; no word, answer, skill,
or semantic content is added.
"""

from __future__ import annotations

from db.database import SessionLocal
from db.models import ContentAssetLink, ContentItem, ContentOption

LETTER_FORM_ITEM = "L1-CORE-03"
LETTER_FORM_POOL = ["بـ", "مـ", "سـ", "كـ", "لـ"]

L1_WORD_IMAGE_ITEM = "L1-REIN-03"
L1_WORD_IMAGE_POOL = ["باب", "قلم", "شمس", "سمكة", "كرة"]

L2_WORD_IMAGE_ITEM = "L2-REIN-04"
L2_WORD_IMAGE_POOL = ["بَاب", "قَلَم", "شَمْس", "قِطَّة", "كِتَاب"]

POST_LETTER_ELEMENT_ITEM = "POST-Q08"
POST_LETTER_ELEMENT_POOL = ["ل", "كِتَاب", "قَرَأَ خَالِدٌ الْكِتَابَ."]
POST_WORD_ELEMENT_ITEM = "POST-Q09"
POST_WORD_ELEMENT_POOL = ["ك", "نَخْلَة", "ذَهَبَ مَاجِدٌ إِلَى الْبَحْرِ"]

L3_APPROVED_ROUND_CHOICES = {
    "L3-CORE-07": [
        ["المكتبة", "الحديقة", "الساحة"],
        ["وقت الفسحة", "في الليل", "بعد العودة إلى البيت"],
        ["الحيوانات", "السيارات", "الطعام"],
        ["أمين المكتبة", "صديقه", "والده"],
        ["أعاده إلى مكانه", "تركه على الأرض", "أخذه إلى البيت"],
    ],
    "L3-CORE-08": [
        ["لأنهم سيقضون وقتًا في الرحلة", "ليغسل السيارة", "ليرويه على الأرض"],
        ["لوضع حاجاتهم فيها", "لتركها في الوادي", "للعب بها"],
        ["المحافظة على النظافة", "الرغبة في العودة سريعًا", "الخوف من الطيور"],
        ["تنظيف المكان قبل المغادرة", "ترك الطعام على الأرض", "قطع الأشجار"],
        ["رحلة عائلية مع المحافظة على المكان", "يوم دراسي داخل الفصل", "التسوق من السوق"],
    ],
    "L3-CORE-09": [
        ["قليل الضوضاء", "سريع الحركة", "شديد الحرارة"],
        ["أرجع", "أخذ", "كسر"],
        ["أشياء متروكة بعد الاستخدام", "أدوات الدراسة", "أنواع النباتات"],
        ["نظيفة وواضحة", "مظلمة", "بعيدة"],
        ["بجانب", "فوق", "بعيدًا عن"],
    ],
    "L3-REIN-02": [
        ["حمل سالم مظلته وخرج من المنزل", "لعب سالم بالكرة", "قرأ سالم كتابًا"],
        ["كانت تسقيها كل صباح", "كانت تنظر إلى السماء", "كانت تلعب في الساحة"],
        ["أعاد الكتاب إلى مكانه", "دخل المكتبة", "جلس على الكرسي"],
    ],
    "L3-REIN-05": [
        ["في المكتبة", "في الملعب", "رحلة إلى البحر"],
        ["شاطئ نظيف", "يوم في المدرسة", "زيارة الطبيب"],
        ["النبتة الصغيرة", "السيارة الجديدة", "الطائر السريع"],
    ],
}

# The approved source requires *three displays* for each sentence but provides
# only the correct segmentation. These distractors change slash boundaries only.
# They deliberately preserve every approved word and word order.
L3_SEGMENTATION_ROUNDS = [
    [
        "ذَهَبَ سَالِمٌ / إِلَى الْمَدْرَسَةِ / فِي الصَّبَاحِ",
        "ذَهَبَ / سَالِمٌ إِلَى الْمَدْرَسَةِ / فِي الصَّبَاحِ",
        "ذَهَبَ سَالِمٌ إِلَى / الْمَدْرَسَةِ فِي / الصَّبَاحِ",
    ],
    [
        "جَلَسَتْ مَرْيَمُ / تَحْتَ الشَّجَرَةِ / وَقَرَأَتْ كِتَابًا",
        "جَلَسَتْ / مَرْيَمُ تَحْتَ الشَّجَرَةِ / وَقَرَأَتْ كِتَابًا",
        "جَلَسَتْ مَرْيَمُ تَحْتَ / الشَّجَرَةِ وَقَرَأَتْ / كِتَابًا",
    ],
    [
        "لَعِبَ الْأَطْفَالُ / فِي السَّاحَةِ / بَعْدَ الدَّرْسِ",
        "لَعِبَ / الْأَطْفَالُ فِي السَّاحَةِ / بَعْدَ الدَّرْسِ",
        "لَعِبَ الْأَطْفَالُ فِي / السَّاحَةِ بَعْدَ / الدَّرْسِ",
    ],
    [
        "وَقَفَ الْعُصْفُورُ / فَوْقَ النَّخْلَةِ / ثُمَّ طَارَ",
        "وَقَفَ / الْعُصْفُورُ فَوْقَ النَّخْلَةِ / ثُمَّ طَارَ",
        "وَقَفَ الْعُصْفُورُ فَوْقَ / النَّخْلَةِ ثُمَّ / طَارَ",
    ],
    [
        "عَادَ مَاجِدٌ / إِلَى الْبَيْتِ / مَعَ وَالِدِهِ",
        "عَادَ / مَاجِدٌ إِلَى الْبَيْتِ / مَعَ وَالِدِهِ",
        "عَادَ مَاجِدٌ إِلَى / الْبَيْتِ مَعَ / وَالِدِهِ",
    ],
]

WORD_IMAGE_ASSETS = {
    "باب": "VOC-03",
    "بَاب": "VOC-03",
    "قلم": "VOC-04",
    "قَلَم": "VOC-04",
    "شمس": "VOC-06",
    "شَمْس": "VOC-06",
    "سمكة": "VOC-05",
    "كرة": "VOC-10",
    "قِطَّة": "VOC-16",
    "كتاب": "VOC-02",
    "كِتَاب": "VOC-02",
}


def _find_item(db, canonical: str) -> ContentItem | None:
    direct = db.query(ContentItem).filter(ContentItem.stable_key == canonical).first()
    if direct is not None:
        return direct
    return next(
        (
            item
            for item in db.query(ContentItem).all()
            if str((item.template_data or {}).get("canonical_id") or "") == canonical
        ),
        None,
    )


def _plain(value: str) -> str:
    import re
    return re.sub(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]", "", value or "").replace("ـ", "")


def _ensure_option_count(step, *, pool: list[str], total: int) -> int:
    existing = sorted(step.options, key=lambda value: value.order_index)
    if not existing:
        raise RuntimeError(f"Step {step.id} has no approved correct option")

    correct = next((option for option in existing if option.is_correct), existing[0])
    current_texts = {option.text for option in existing}
    normalized_correct = _plain(correct.text)
    distractors = [value for value in pool if _plain(value) != normalized_correct]
    if len(distractors) < total - 1:
        raise RuntimeError(f"Not enough approved distractors for step {step.id}")

    offset = max(0, int(step.order_index) - 1) % len(distractors)
    rotated = distractors[offset:] + distractors[:offset]
    created = 0
    for value in rotated:
        if len(current_texts) >= total:
            break
        normalized_current = {_plain(text) for text in current_texts}
        if value in current_texts or _plain(value) in normalized_current:
            continue
        step.options.append(ContentOption(
            text=value,
            is_correct=False,
            order_index=len(current_texts) + 1,
        ))
        current_texts.add(value)
        created += 1
    return created


def _asset_for_word(value: str) -> str | None:
    direct = WORD_IMAGE_ASSETS.get(value)
    if direct:
        return direct
    plain = _plain(value)
    for label, asset_id in WORD_IMAGE_ASSETS.items():
        if _plain(label) == plain:
            return asset_id
    return None


def _ensure_word_image_assets(step) -> int:
    created = 0
    existing_ids = {
        link.manifest_asset_id
        for link in step.assets
        if link.asset_type == "image" and link.usage_context == "choice"
    }
    for option in sorted(step.options, key=lambda value: value.order_index):
        asset_id = _asset_for_word(option.text)
        if not asset_id or asset_id in existing_ids:
            continue
        step.assets.append(ContentAssetLink(
            manifest_asset_id=asset_id,
            asset_type="image",
            usage_context="choice",
        ))
        existing_ids.add(asset_id)
        created += 1
    return created


def _repair_image_choice(db, canonical: str, pool: list[str], *, interaction: str) -> int:
    item = _find_item(db, canonical)
    if item is None:
        return 0
    data = dict(item.template_data or {})
    if data.get("canonical_interaction_type") != interaction:
        data["canonical_interaction_type"] = interaction
        item.template_data = data
    created = 0
    for step in sorted(item.steps, key=lambda value: value.order_index):
        created += _ensure_option_count(step, pool=pool, total=3)
        created += _ensure_word_image_assets(step)
    return created


def _repair_text_choice(db, canonical: str, pool: list[str], *, total: int) -> int:
    item = _find_item(db, canonical)
    if item is None:
        return 0
    created = 0
    for step in sorted(item.steps, key=lambda value: value.order_index):
        created += _ensure_option_count(step, pool=pool, total=total)
    return created


def _repair_round_choices(db, canonical: str, approved_rounds: list[list[str]]) -> int:
    item = _find_item(db, canonical)
    if item is None:
        return 0
    steps = sorted(item.steps, key=lambda value: value.order_index)
    if len(steps) != len(approved_rounds):
        raise RuntimeError(
            f"{canonical} round count mismatch: runtime={len(steps)} approved={len(approved_rounds)}"
        )
    created = 0
    for step, choices in zip(steps, approved_rounds, strict=True):
        created += _ensure_option_count(step, pool=choices, total=len(choices))
    return created


def run_seed() -> int:
    db = SessionLocal()
    created = 0
    try:
        letter_forms = _find_item(db, LETTER_FORM_ITEM)
        if letter_forms is not None:
            for step in sorted(letter_forms.steps, key=lambda value: value.order_index):
                created += _ensure_option_count(step, pool=LETTER_FORM_POOL, total=4)

        created += _repair_image_choice(
            db,
            L1_WORD_IMAGE_ITEM,
            L1_WORD_IMAGE_POOL,
            interaction="listen_choose_image",
        )
        created += _repair_image_choice(
            db,
            L2_WORD_IMAGE_ITEM,
            L2_WORD_IMAGE_POOL,
            interaction="choose_image",
        )
        created += _repair_text_choice(
            db,
            POST_LETTER_ELEMENT_ITEM,
            POST_LETTER_ELEMENT_POOL,
            total=3,
        )
        created += _repair_text_choice(
            db,
            POST_WORD_ELEMENT_ITEM,
            POST_WORD_ELEMENT_POOL,
            total=3,
        )
        for canonical, approved_rounds in L3_APPROVED_ROUND_CHOICES.items():
            created += _repair_round_choices(db, canonical, approved_rounds)
        created += _repair_round_choices(db, "L3-REIN-01", L3_SEGMENTATION_ROUNDS)

        db.commit()
        return created
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print(f"Created {run_seed()} approved choice-presentation corrections")
