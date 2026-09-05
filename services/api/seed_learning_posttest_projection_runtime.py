"""Deterministic structured projection for learning and posttest presentation.

The approved/versioned source is imported into PostgreSQL before this projection
runs. Student-facing learning metadata is therefore built from structured DB
runtime fields and explicit approved overrides only; legacy ``prompt_text`` is
never parsed to infer a question, stimulus, hint, option, or answer.
"""
from __future__ import annotations

from typing import Any

import seed_learning_posttest_experience_2026_09_01 as base
from content_runtime import round_data as runtime_round_data
from db.models import ContentItem

LEARNING_VERSION = "HIMMA-LEARNING-2026-09-01-R2"
POSTTEST_VERSION = base.POSTTEST_VERSION
PROJECTION_CONTRACT = "structured_db_runtime_v1"

READ = {"read_aloud", "timed_read_aloud"}
LISTEN = {"listen_choose_one", "listen_choose_image", "listen_choose_many"}
ORDER = {"sequence", "memory_sequence", "build_word"}
NO_TEXT_STIMULUS = READ | LISTEN | ORDER | {"choose_image", "choose_many"}

# Original 105-item source rounds predate the structured projection schema.
# These values are explicit, source-derived display fields for the small subset
# of original choice activities that require a visible textual stimulus. They
# intentionally contain only what the learner may see, never the serialized
# answer/choice portion of the legacy source line.
BASE_VISIBLE_STIMULI: dict[str, tuple[str, ...]] = {
    "L1-CORE-01": ("ب", "ج", "س", "ق", "د"),
    "L1-CORE-03": ("ب", "م", "س", "ك", "ل"),
    "L1-CORE-07": ("ب", "كِتَاب", "ذَهَبَ سَالِمٌ.", "م", "شَجَرَة"),
    "L1-REIN-01": ("ب", "ج", "س", "ق", "د"),
    "L2-REIN-01": ("_اب", "ق_م", "س_ك", "كِتَا_", "نُ_ر"),
    "L3-CORE-09": ("هَادِئ", "أَعَادَ", "مُخَلَّفَات", "صَافِيَة", "قُرْبَ"),
    "L3-REIN-02": ("المطر", "اهتمام مريم", "حفاظ خالد على الكتب"),
}

BASE_ROUND_QUESTIONS: dict[str, tuple[str, ...]] = {
    "L3-CORE-07": (
        "أين دخل خالد؟",
        "متى دخل؟",
        "عن ماذا كان يبحث؟",
        "من ساعده؟",
        "ماذا فعل بالكتاب؟",
    ),
    "L3-CORE-08": (
        "لماذا أحضر الأب الماء؟",
        "لماذا حمل الأطفال حقائبهم؟",
        "ماذا يدل جمع المخلفات؟",
        "ما السلوك الصحيح؟",
        "اختر الفكرة العامة للنص.",
    ),
}

PROJECTION_ITEM_OVERRIDES: dict[str, dict[str, str]] = {
    "L1-REIN-07": {
        "question": "اختر الشكل الآخر للحرف نفسه.",
        "instruction": "انظر إلى الحرف، ثم اختر الشكل الصحيح له من الخيارات.",
        "hint": "ركّز في شكل الحرف نفسه، ولا تعتمد على موقعه فقط.",
    },
    "L1-REIN-09": {
        "question": "هل العنصر حرف أم كلمة أم جملة؟",
        "instruction": "انظر إلى العنصر، ثم اختر التصنيف المناسب.",
        "hint": "لاحظ هل هو رمز واحد، كلمة واحدة، أم جملة كاملة.",
    },
    "L2-REIN-01": {
        "question": "اختر الحرف الناقص لإكمال الكلمة.",
        "instruction": "انظر إلى الكلمة الناقصة، ثم اختر الحرف الذي يكملها.",
        "hint": "اقرأ ما يظهر من الكلمة، ثم جرّب الحرف الذي يجعلها كلمة صحيحة.",
    },
    "L2-REIN-09": {
        "question": "اختر الكلمة المكتوبة بالشدة بشكل صحيح.",
        "instruction": "قارن بين الكلمتين، ثم اختر الكتابة الصحيحة للشدة.",
        "hint": "ركّز على موضع علامة الشدة فوق الحرف.",
    },
    "L3-CORE-07": {
        "instruction": "ارجع إلى النص، ثم اختر الإجابة الموجودة فيه.",
        "hint": "ابحث في النص عن المعلومة التي يطلبها السؤال.",
    },
    "L3-CORE-08": {
        "instruction": "اقرأ السؤال، ثم اختر الإجابة الأنسب اعتمادًا على النص.",
        "hint": "فكّر في معنى الحدث وما يدل عليه داخل النص.",
    },
    "L3-CORE-09": {
        "question": "اختر معنى الكلمة.",
        "instruction": "انظر إلى الكلمة، ثم اختر معناها الصحيح.",
        "hint": "فكّر في معنى الكلمة داخل الجملة أو السياق الذي تعلمته.",
    },
    "L3-REIN-01": {
        "question": "اختر التقسيم الصحيح للجملة.",
        "instruction": "انظر إلى الخيارات، ثم اختر التقسيم الذي يحافظ على وحدات المعنى.",
        "hint": "اجمع الكلمات التي تكوّن معنى واحدًا قبل الانتقال إلى الجزء التالي.",
    },
    "L3-REIN-02": {
        "question": "اختر جملة الدليل المناسبة.",
        "instruction": "اقرأ المطلوب، ثم اختر الجملة التي تقدّم الدليل المناسب.",
        "hint": "ابحث عن الجملة التي تثبت المعنى المطلوب مباشرة.",
    },
    "L3-REIN-05": {
        "question": "اختر عنوان النص المناسب.",
        "instruction": "اقرأ النص أو شاهده، ثم اختر العنوان الذي يلخص فكرته.",
        "hint": "اختر العنوان الذي يجمع الفكرة الأهم في النص.",
    },
    "L3-REIN-09": {
        "question": "اختر معنى الكلمة من الجملة.",
        "instruction": "اقرأ الجملة والسؤال، ثم اختر المعنى المناسب من الخيارات.",
        "hint": "استخدم معنى الجملة لتعرف المقصود من الكلمة.",
    },
}

SAFE_HINT_OVERRIDES = {
    "L1-CORE-07": "لاحظ حجم العنصر وعدد الرموز والمسافات بين أجزائه، ثم اختر التصنيف المناسب.",
}


def _round_value(values: tuple[str, ...] | None, round_number: int) -> str | None:
    if not values:
        return None
    index = round_number - 1
    if index < 0 or index >= len(values):
        raise RuntimeError(f"Structured projection round {round_number} is outside explicit source data")
    return values[index]


def _source_round(item: ContentItem, step) -> dict[str, Any]:
    source = runtime_round_data(item, step)
    if not source:
        raise RuntimeError(f"{base.canonical(item)} is missing db_runtime source data for round {step.order_index}")
    return source


def _generic_question(interaction: str) -> str:
    if interaction in LISTEN:
        return "استمع جيدًا، ثم اختر الإجابة المناسبة."
    if interaction in READ:
        return "اقرأ النص المعروض بصوت واضح."
    if interaction == "memory_sequence":
        return "تذكّر ترتيب الصور."
    if interaction == "sequence":
        return "رتّب العناصر بالترتيب الصحيح."
    if interaction == "build_word":
        return "ابنِ الكلمة بالترتيب الصحيح."
    if interaction == "choose_image":
        return "انظر إلى الصور، ثم اختر الصورة المناسبة."
    if interaction == "choose_many":
        return "اختر العناصر المطلوبة."
    return "اختر الإجابة المناسبة."


def _generic_instruction(interaction: str) -> str:
    if interaction in LISTEN:
        return "اضغط زر الاستماع، ثم اختر الإجابة المطابقة."
    if interaction in READ:
        return "اضغط زر التسجيل، اقرأ النص المعروض، ثم أرسل التسجيل."
    if interaction == "memory_sequence":
        return "شاهد الصور جيدًا، ثم اضغط «التالي» عندما تكون مستعدًا لإعادة ترتيبها."
    if interaction == "sequence":
        return "اضغط العناصر بحسب ترتيبها الصحيح."
    if interaction == "build_word":
        return "اضغط الحروف أو المقاطع بالترتيب حتى تكتمل الكلمة."
    if interaction in {"choose_image", "choose_many"}:
        return "انظر إلى العناصر المعروضة، ثم اختر المطلوب."
    return "اقرأ المطلوب، ثم اختر الإجابة المناسبة."


def _generic_hint(interaction: str) -> str:
    if interaction == "memory_sequence":
        return "تذكّر الصورة الأولى، ثم التي بعدها."
    if interaction == "sequence":
        return "ابدأ بما حدث أولًا، ثم أكمل الترتيب خطوة خطوة."
    if interaction == "build_word":
        return "ابدأ بالحرف أو المقطع الذي تبدأ به الكلمة."
    if interaction in READ:
        return "اقرأ ببطء ووضوح، وركّز في الحروف والحركات."
    if interaction in LISTEN:
        return "استمع مرة أخرى، وركّز في الصوت المطلوب."
    if interaction in {"choose_image", "choose_many"}:
        return "انظر إلى كل عنصر بهدوء قبل أن تختار."
    return "اقرأ المطلوب بهدوء، ثم اختر الإجابة الأنسب."


def _structured_stimulus(item: ContentItem, step, interaction: str, source: dict[str, Any]) -> str:
    key = base.canonical(item)
    round_number = int(step.order_index)

    explicit = _round_value(BASE_VISIBLE_STIMULI.get(key), round_number)
    if explicit is not None:
        return explicit

    if key in {"L3-REIN-01", "L3-REIN-05"}:
        return ""

    # Maintenance-approved v1/v2 additions already carry a dedicated structured
    # ``prompt`` field. It is safe to project directly because options/answers
    # are stored separately instead of serialized into the prompt.
    prompt = source.get("prompt")
    if interaction == "choose_one" and isinstance(prompt, str):
        return prompt.strip()

    if interaction in NO_TEXT_STIMULUS:
        return ""
    return ""


def _onset_pair_round(item: ContentItem, step, total: int) -> dict[str, Any] | None:
    pair = dict((item.template_data or {}).get("onset_pair_compare") or {})
    if not pair:
        return None
    rounds = list(pair.get("rounds") or [])
    index = int(step.order_index) - 1
    if index < 0 or index >= len(rounds):
        raise RuntimeError(f"{base.canonical(item)} onset pair round mismatch")
    return {
        "round_number": int(step.order_index),
        "round_total": total,
        "skill": str(pair.get("skill") or "التمييز السمعي بين بدايات الكلمات"),
        "encouragement": base.encouragement(int(step.order_index), total),
        "hint": "ركّز على بداية الكلمة الأولى ثم بداية الكلمة الثانية.",
        "question_text": str(pair.get("student_question") or "استمع إلى الكلمتين، ثم قارن بدايتهما."),
        "instruction_text": str(pair.get("instruction") or "استمع إلى الكلمتين كاملتين، ثم قارن أول صوت في كل كلمة."),
        "stimulus_text": "",
    }


def _auditory_story_round(item: ContentItem, step, total: int) -> dict[str, Any] | None:
    story = dict((item.template_data or {}).get("auditory_story") or {})
    if not story:
        return None
    rounds = list(story.get("rounds") or [])
    index = int(step.order_index) - 1
    if index < 0 or index >= len(rounds):
        raise RuntimeError(f"{base.canonical(item)} auditory story round mismatch")
    round_spec = dict(rounds[index])
    return {
        "round_number": int(step.order_index),
        "round_total": total,
        "skill": str(story.get("skill") or "الفهم السمعي المباشر"),
        "encouragement": base.encouragement(int(step.order_index), total),
        "hint": str(round_spec.get("hint") or ""),
        "question_text": str(round_spec.get("question_text") or ""),
        "instruction_text": str(round_spec.get("instruction_text") or ""),
        "stimulus_text": "",
    }


def _learning_round(item: ContentItem, step, total: int) -> dict[str, Any]:
    onset_pair = _onset_pair_round(item, step, total)
    if onset_pair is not None:
        return onset_pair
    auditory = _auditory_story_round(item, step, total)
    if auditory is not None:
        return auditory

    key = base.canonical(item)
    interaction = str((item.template_data or {}).get("canonical_interaction_type") or item.interaction_type)
    source = _source_round(item, step)
    base_override = dict(base.ITEM_OVERRIDES.get(key, {}))
    projection_override = dict(PROJECTION_ITEM_OVERRIDES.get(key, {}))
    round_number = int(step.order_index)

    round_question = _round_value(BASE_ROUND_QUESTIONS.get(key), round_number)
    question = str(
        round_question
        or projection_override.get("question")
        or base_override.get("question")
        or _generic_question(interaction)
    )
    instruction = str(
        projection_override.get("instruction")
        or base_override.get("instruction")
        or _generic_instruction(interaction)
    )
    hint = str(
        SAFE_HINT_OVERRIDES.get(key)
        or projection_override.get("hint")
        or base_override.get("hint")
        or _generic_hint(interaction)
    )
    title = str((item.template_data or {}).get("title") or item.stable_key)

    return {
        "round_number": round_number,
        "round_total": total,
        "skill": projection_override.get("skill") or base_override.get("skill") or title,
        "encouragement": base.encouragement(round_number, total),
        "hint": hint,
        "question_text": question,
        "instruction_text": instruction,
        "stimulus_text": _structured_stimulus(item, step, interaction, source),
    }


def _apply_learning_r2(db) -> int:
    items = db.query(ContentItem).filter(ContentItem.kind.in_(["core_activity", "reinforcement_activity"])).all()
    if len(items) != 65:
        raise RuntimeError(f"Expected 65 learning items, got {len(items)}")
    changed = 0
    for item in items:
        steps = sorted(item.steps, key=lambda step: step.order_index)
        if not steps:
            raise RuntimeError(f"{base.canonical(item)} has no rounds")
        data = dict(item.template_data or {})
        projected = dict(data)
        projected["learning_experience_version"] = LEARNING_VERSION
        projected["learning_experience"] = {
            "version": LEARNING_VERSION,
            "projection_contract": PROJECTION_CONTRACT,
            "rounds": [_learning_round(item, step, len(steps)) for step in steps],
        }
        if projected != data:
            item.template_data = projected
            changed += 1
    return changed


base.learning_round = _learning_round
base.apply_learning = _apply_learning_r2
base.LEARNING_VERSION = LEARNING_VERSION
run_seed = base.run_seed
