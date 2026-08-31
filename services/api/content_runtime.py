"""Canonical Himma content projection for student-facing runtimes.

The approved baseline catalog remains the semantic source of truth for the
original 105 items. Maintenance-approved reinforcement additions are projected
additively so their canonical interactions and approved/reused media behave like
baseline content without rewriting the client source catalog.

The student-facing presentation layer in this module is intentionally derived
from the approved semantic intent. It does not change answers, scoring, skill
mapping, or activity order. Its job is only to turn terse/internal labels into
clear Arabic instructions that a Grade-3 learner can understand.
"""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from db.models import ContentItem, ContentStep

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "packages" / "content" / "src" / "catalog.json"
ADDITION_PATHS = (
    REPO_ROOT / "packages" / "content" / "src" / "reinforcement_additions_v1.json",
    REPO_ROOT / "packages" / "content" / "src" / "reinforcement_additions_v2.json",
)
VISUAL_PLAN_PATH = REPO_ROOT / "packages" / "content" / "src" / "visual_asset_plan_v1.json"
AUDIO_MANIFEST = REPO_ROOT / "assets" / "audio" / "HIMMA_AUDIO_V1" / "manifest.csv"
IMAGE_MAP = REPO_ROOT / "assets" / "education" / "developer" / "asset-map.json"


def _read_json(path: Path, *, required: bool = True) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        if required:
            raise RuntimeError(f"Approved content metadata is unavailable: {path.name}") from exc
        return {}


def semantic_key(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = re.sub(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]", "", value)
    value = value.replace("ـ", "")
    value = re.sub(r"[^\w\u0600-\u06ff]+", "", value, flags=re.UNICODE)
    if value.startswith("ال"):
        value = value[2:]
    return value.casefold()


def _audio_index() -> dict[str, str]:
    index: dict[str, str] = {}
    try:
        with AUDIO_MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("status") != "approved":
                    continue
                asset_id = str(row.get("id") or "").strip()
                if not asset_id:
                    continue
                for value in (row.get("text_ar"), row.get("spoken_input")):
                    key = semantic_key(str(value or ""))
                    if key:
                        index.setdefault(key, asset_id)
    except OSError:
        pass
    return index


def _image_index() -> dict[str, str]:
    index: dict[str, str] = {}
    payload = _read_json(IMAGE_MAP, required=False)
    for asset in payload.get("assets", []):
        asset_id = str(asset.get("id") or "").strip()
        if not asset_id:
            continue
        for value in (asset.get("label_ar"), asset.get("alt_ar")):
            key = semantic_key(str(value or ""))
            if key:
                index.setdefault(key, asset_id)
    return index


_AUDIO_BY_TEXT = _audio_index()
_IMAGE_BY_TEXT = _image_index()
_VISUAL_PLAN = _read_json(VISUAL_PLAN_PATH, required=False)


def _project_addition(item: dict[str, Any]) -> dict[str, Any]:
    projected = dict(item)
    canonical = str(item.get("canonical_id") or "")
    interaction = str(item.get("interaction") or "")
    explicit_reuse = (_VISUAL_PLAN.get("reuse") or {}).get(canonical, {})
    new_audio_required = {
        semantic_key(str(value))
        for value in (item.get("media") or {}).get("new_audio_required", [])
    }

    rounds: list[dict[str, Any]] = []
    for order_index, source_round in enumerate(item.get("rounds", []), start=1):
        round_data = dict(source_round)
        round_data["order_index"] = order_index
        media: list[dict[str, Any]] = []
        media_gaps: list[dict[str, Any]] = []

        audio_text = str(round_data.get("audio_text") or "").strip()
        if audio_text:
            asset_id = _AUDIO_BY_TEXT.get(semantic_key(audio_text))
            if asset_id:
                media.append({
                    "asset_id": asset_id,
                    "type": "audio",
                    "usage": "prompt",
                    "semantic_text": audio_text,
                })
            elif semantic_key(audio_text) in new_audio_required:
                media_gaps.append({
                    "asset_type": "audio",
                    "usage": "prompt",
                    "semantic_text": audio_text,
                    "status": "missing_approved_asset",
                    "reason": "approved reinforcement explicitly requires this new fixed audio asset",
                })

        sequence = round_data.get("sequence")
        if isinstance(sequence, list):
            for value in sequence:
                semantic_text = str(value)
                asset_id = str(explicit_reuse.get(semantic_text) or "").strip()
                if not asset_id and interaction == "memory_sequence":
                    asset_id = _IMAGE_BY_TEXT.get(semantic_key(semantic_text), "")
                if asset_id:
                    media.append({
                        "asset_id": asset_id,
                        "type": "image",
                        "usage": "illustration",
                        "semantic_text": semantic_text,
                    })

        if media:
            round_data["media"] = media
        if media_gaps:
            round_data["media_gaps"] = media_gaps
        rounds.append(round_data)

    projected["rounds"] = rounds
    return projected


def _load_runtime_catalog() -> dict[str, Any]:
    baseline = _read_json(CATALOG_PATH)
    items = list(baseline.get("items", []))
    for additions_path in ADDITION_PATHS:
        additions = _read_json(additions_path, required=False)
        for item in additions.get("items", []):
            items.append(_project_addition(item))
    return {**baseline, "items": items}


_CATALOG = _load_runtime_catalog()
_ITEMS = {item["canonical_id"]: item for item in _CATALOG.get("items", [])}
_ROUNDS = {
    (item["canonical_id"], int(round_data["order_index"])): round_data
    for item in _CATALOG.get("items", [])
    for round_data in item.get("rounds", [])
    if round_data.get("order_index") is not None
}
_SKILL_CODES = {
    str(skill.get("skill_id")): str(skill.get("skill_code") or "")
    for skill in _CATALOG.get("skills", [])
    if skill.get("skill_id")
}


def canonical_id(item: ContentItem) -> str:
    data = item.template_data or {}
    return str(data.get("canonical_id") or item.stable_key)


def canonical_interaction(item: ContentItem) -> str:
    data = item.template_data or {}
    return str(data.get("canonical_interaction_type") or item.interaction_type)


def catalog_item(item: ContentItem) -> dict[str, Any]:
    return _ITEMS.get(canonical_id(item), {})


def round_data(item: ContentItem, step: ContentStep) -> dict[str, Any]:
    return _ROUNDS.get((canonical_id(item), int(step.order_index)), {})


def _skill_code(item: ContentItem) -> str:
    data = catalog_item(item)
    skill_id = str(data.get("skill_id") or "")
    if skill_id and skill_id in _SKILL_CODES:
        return _SKILL_CODES[skill_id]
    return str(data.get("target_skill_family") or data.get("skill_code") or "")


def _round_text(item: ContentItem, step: ContentStep) -> str:
    data = round_data(item, step)
    for key in ("source_text", "prompt", "question", "instruction"):
        value = str(data.get(key) or "").strip()
        if value:
            return value
    return str(step.prompt_text or "").strip()


def _extract_instruction(source: str) -> str:
    if not source:
        return ""
    match = re.search(r"(?:التعليمات(?: للطالب)?|التعليمة)\s*:\s*(.+?)(?=\s*(?:الخيارات|الصور|الإجابة|طريقة الإجابة|$)\s*:|$)", source, flags=re.S)
    if match:
        return " ".join(match.group(1).split()).strip(" .")
    return ""


def _extract_question(source: str) -> str:
    if not source:
        return ""
    match = re.search(r"السؤال\s*:\s*(.+?)(?=\s*(?:الخيارات|الإجابة|طريقة الإجابة|$)\s*:|$)", source, flags=re.S)
    if match:
        return " ".join(match.group(1).split()).strip(" .")
    return ""


def _fallback_instruction(interaction: str) -> str:
    return {
        "choose_one": "اقرأ المطلوب، ثم اختر إجابة واحدة.",
        "listen_choose_one": "استمع أولًا، ثم اختر الإجابة التي تطابق ما سمعته.",
        "choose_image": "انظر جيدًا، ثم اختر الصورة المطلوبة.",
        "listen_choose_image": "استمع أولًا، ثم اختر الصورة التي تطابق ما سمعته.",
        "choose_many": "اقرأ المطلوب، ثم اختر كل العناصر الصحيحة.",
        "listen_choose_many": "استمع أولًا، ثم اختر كل العناصر التي تطابق ما سمعته.",
        "sequence": "اضغط على العناصر واحدًا بعد الآخر بالترتيب الصحيح.",
        "memory_sequence": "تذكّر الصور جيدًا، ثم أعد ترتيبها كما ظهرت.",
        "path_sequence": "ابدأ من اليمين، ثم اتبع المسار نقطةً بعد نقطة.",
        "build_word": "اضغط على الحروف بالترتيب حتى تكوّن الكلمة المطلوبة.",
        "timed_read_aloud": "اقرأ النص بصوت واضح وطبيعي عند بدء التسجيل.",
        "read_aloud": "اقرأ النص الظاهر بصوت واضح، ثم أرسل تسجيلك.",
    }.get(interaction, "اقرأ المطلوب بهدوء، ثم أكمل المهمة.")


def instruction_text(item: ContentItem, step: ContentStep) -> str:
    """Return a child-clear instruction without changing the approved task intent."""
    interaction = canonical_interaction(item)
    skill = _skill_code(item)
    source = _round_text(item, step)
    explicit_instruction = _extract_instruction(source)
    explicit_question = _extract_question(source)

    if skill in {"visual_letter_discrimination", "similar_letter_discrimination"}:
        return explicit_instruction or "انظر إلى الحروف، ثم اضغط على الحرف المطلوب."
    if skill == "letter_form_recognition":
        return "انظر إلى الحرف، ثم اختر الشكل الآخر للحرف نفسه."
    if skill == "sound_symbol_mapping":
        return "استمع إلى صوت الحرف، ثم اختر الحرف الذي يطابق هذا الصوت."
    if skill == "initial_sound_isolation":
        if interaction in {"choose_image", "listen_choose_image"}:
            return "استمع إلى صوت الحرف، ثم اختر الصورة التي يبدأ اسمها بهذا الصوت."
        return "استمع إلى الكلمة، ثم اختر الحرف الذي تسمعه في بدايتها."
    if skill == "final_sound_isolation":
        return "استمع إلى الكلمة، ثم اختر الحرف الذي تسمعه في آخرها."
    if skill == "word_onset_comparison":
        return "استمع إلى الصوت والكلمة، ثم قارن الصوت بأول حرف في الكلمة: هل هما متشابهان أم مختلفان؟"
    if skill == "print_concepts":
        return explicit_instruction or "انظر إلى العناصر، ثم اضغط على العنصر المطلوب."
    if skill in {"logical_sequence", "event_order", "sequence_order"}:
        return "انظر إلى الصور، ثم اضغط عليها حسب ترتيب حدوثها من البداية إلى النهاية."
    if skill == "visual_memory":
        return "انظر إلى الصور وتذكّر ترتيبها، ثم أعد ترتيبها كما ظهرت."
    if skill in {"auditory_vocabulary", "auditory_word_discrimination"}:
        if interaction in {"choose_image", "listen_choose_image"}:
            return "استمع إلى الكلمة، ثم اختر الصورة التي تعبّر عنها."
        return "استمع إلى الكلمة، ثم اختر الكلمة التي سمعتها."
    if skill == "short_vowels":
        return "استمع إلى المقطع، ثم اختر المقطع الذي يحمل الحركة نفسها التي سمعتها."
    if skill in {"long_vowels", "madd_word_reading"}:
        return "استمع إلى الصوت، ثم اختر المقطع أو الكلمة التي تطابق صوت المد الذي سمعته."
    if skill in {"syllable_blending", "syllable_reading"} and interaction in {"choose_many", "listen_choose_many"}:
        return "اختر المقاطع التي تكوّن الكلمة المطلوبة، واضغط عليها بالترتيب."
    if skill in {"word_building", "letter_order"} or interaction == "build_word":
        return explicit_instruction or "اضغط على الحروف بالترتيب حتى تكوّن الكلمة المطلوبة."
    if skill == "sentence_building":
        return "رتّب الكلمات حتى تكوّن جملة صحيحة وواضحة."
    if skill == "word_completion":
        return "انظر إلى الكلمة الناقصة، ثم اختر الحرف الذي يكملها بشكل صحيح."
    if skill == "word_image_comprehension":
        return "اقرأ الكلمة، ثم اختر الصورة التي تطابق معناها."
    if skill == "tanween":
        return "استمع أو اقرأ جيدًا، ثم اختر الشكل الذي يحمل التنوين المطلوب."
    if skill in {"letter_reading", "general_word_reading", "short_vowel_word_reading", "sukoon_word_reading", "shadda_word_reading", "sentence_reading"}:
        if interaction in {"read_aloud", "timed_read_aloud"}:
            return "اقرأ النص الظاهر بصوت واضح، ثم أرسل تسجيلك."
    if skill in {"literal_comprehension", "inferential_comprehension", "main_idea", "text_evidence", "word_meaning"}:
        if explicit_question:
            return f"اقرأ السؤال جيدًا، ثم اختر الإجابة: {explicit_question}"
        return "اقرأ النص والسؤال جيدًا، ثم اختر الإجابة التي يدل عليها النص."
    if interaction in {"read_aloud", "timed_read_aloud"}:
        return _fallback_instruction(interaction)
    if explicit_instruction:
        return explicit_instruction
    return _fallback_instruction(interaction)


def media_gaps(item: ContentItem, step: ContentStep) -> list[dict[str, Any]]:
    return list(round_data(item, step).get("media_gaps", []))


def _option_for_semantic(step: ContentStep, semantic_text: str | None, position: int) -> int | None:
    if not step.options:
        return None
    semantic = semantic_key(semantic_text or "")
    if semantic:
        exact = [option for option in step.options if semantic_key(option.text) == semantic]
        if exact:
            return exact[0].id
        contained = [
            option
            for option in step.options
            if semantic in semantic_key(option.text) or semantic_key(option.text) in semantic
        ]
        if contained:
            return contained[0].id
    if position < len(step.options):
        return step.options[position].id
    return None


def _project_approved_media_without_links(item: ContentItem, step: ContentStep) -> list[dict[str, Any]]:
    """Project maintenance-approved additive media without mutating baseline DB rows."""
    if not (item.template_data or {}).get("maintenance_addition"):
        return []
    result: list[dict[str, Any]] = []
    image_position = 0
    for media in round_data(item, step).get("media", []):
        asset_id = str(media.get("asset_id") or "").strip()
        asset_type = str(media.get("type") or "").strip()
        if not asset_id or not asset_type:
            continue
        semantic_text = media.get("semantic_text")
        option_id = None
        if asset_type == "image" and media.get("usage") in {"choice", "illustration"}:
            option_id = _option_for_semantic(step, semantic_text, image_position)
            image_position += 1
        result.append({
            "asset_id": asset_id,
            "asset_type": asset_type,
            "usage": media.get("usage"),
            "semantic_text": semantic_text,
            "url": f"/api/media/{asset_id}",
            "option_id": option_id,
        })
    return result


def step_assets(item: ContentItem, step: ContentStep) -> list[dict[str, Any]]:
    approved = round_data(item, step).get("media", [])
    by_id: dict[str, list[dict[str, Any]]] = {}
    for media in approved:
        by_id.setdefault(str(media.get("asset_id")), []).append(media)

    result: list[dict[str, Any]] = []
    image_position = 0
    for link in step.assets:
        candidates = by_id.get(link.manifest_asset_id, [])
        semantic = candidates.pop(0) if candidates else {}
        option_id = None
        if link.asset_type == "image" and link.usage_context in {"choice", "illustration"}:
            option_id = _option_for_semantic(step, semantic.get("semantic_text"), image_position)
            image_position += 1
        result.append({
            "asset_id": link.manifest_asset_id,
            "asset_type": link.asset_type,
            "usage": link.usage_context,
            "semantic_text": semantic.get("semantic_text"),
            "url": f"/api/media/{link.manifest_asset_id}",
            "option_id": option_id,
        })
    if not result:
        result = _project_approved_media_without_links(item, step)
    return result


def item_assets(item: ContentItem) -> list[dict[str, Any]]:
    approved = catalog_item(item).get("item_assets", [])
    by_id = {str(media.get("asset_id")): media for media in approved}
    return [
        {
            "asset_id": link.manifest_asset_id,
            "asset_type": link.asset_type,
            "usage": link.usage_context,
            "semantic_text": by_id.get(link.manifest_asset_id, {}).get("semantic_text"),
            "url": f"/api/media/{link.manifest_asset_id}",
            "option_id": None,
        }
        for link in item.assets
    ]
