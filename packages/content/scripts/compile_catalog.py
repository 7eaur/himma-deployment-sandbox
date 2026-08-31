#!/usr/bin/env python3
"""Compile the client-approved Himma content document into catalog.json.

The original DOCX remains the academic source of truth.  The checked-in
derived Markdown is a verified, searchable mirror used for deterministic
compilation.  Both source hashes are recorded so drift cannot be silent.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
import uuid
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
ORIGINAL_SOURCE = REPO_ROOT / "reference/original/01_المحتوى_والتخطيط_المعتمد_لمنصة_همة.docx"
DERIVED_SOURCE = REPO_ROOT / "reference/derived/01_المحتوى_والتخطيط_المعتمد_لمنصة_همة.md"
OUTPUT = REPO_ROOT / "packages/content/src/catalog.json"
AUDIO_MANIFEST = REPO_ROOT / "assets/audio/HIMMA_AUDIO_V1/manifest.csv"
IMAGE_MAP = REPO_ROOT / "assets/education/developer/asset-map.json"

CATALOG_VERSION = "HIMMA-CONTENT-1.0"
SCHEMA_VERSION = 1
UUID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "himma.content.v1")

INTERACTIONS = {
    "choose_one",
    "listen_choose_one",
    "choose_image",
    "listen_choose_image",
    "choose_many",
    "listen_choose_many",
    "sequence",
    "memory_sequence",
    "path_sequence",
    "build_word",
    "read_aloud",
    "timed_read_aloud",
}

LEVEL_NAMES = {
    1: "الاستعداد للقراءة",
    2: "بناء الكلمة",
    3: "الطلاقة والفهم",
}

# The approved document intentionally varies wording between tests and activities.
# This explicit taxonomy keeps the original wording while mapping equivalent labels
# to one stable skill.  An unknown label is a hard compilation failure.
SKILL_TAXONOMY: dict[int, list[tuple[str, str, set[str]]]] = {
    1: [
        ("visual_letter_discrimination", "تمييز الحروف بصريًا", {"الانتباه والتمييز البصري", "تمييز الحرف", "تمييز حرف", "تمييز بصري مبسط"}),
        ("similar_letter_discrimination", "تمييز الحروف المتشابهة", {"تمييز الحروف المتشابهة", "تمييز حرف متشابه"}),
        ("letter_form_recognition", "التعرف إلى أشكال الحرف", {"التعرف إلى أشكال الحرف", "التعرف إلى شكل الحرف في أول الكلمة", "شكل الحرف"}),
        ("sound_symbol_mapping", "ربط الصوت بالحرف", {"التمييز السمعي وربط الصوت بالرمز", "ربط الصوت بالحرف", "الصوت والحرف"}),
        ("initial_sound_isolation", "عزل الصوت الأول", {"تحديد الصوت الأول", "عزل الصوت الأول", "الصوت الأول", "صورة تبدأ بالصوت"}),
        ("final_sound_isolation", "عزل الصوت الأخير", {"تحديد الصوت الأخير", "عزل الصوت الأخير", "الصوت الأخير"}),
        ("word_onset_comparison", "مقارنة بدايات الكلمات", {"تمييز بدايات الكلمات"}),
        ("print_concepts", "مفاهيم المادة المطبوعة", {"مفاهيم المادة المطبوعة", "تمييز الكلمة"}),
        ("auditory_vocabulary", "المفردات السمعية", {"المفردات السمعية"}),
        ("visual_memory", "الذاكرة البصرية", {"الذاكرة البصرية والتسلسل"}),
        ("logical_sequence", "التسلسل المنطقي", {"التسلسل المنطقي", "ترتيب صور", "فهم التسلسل"}),
        ("visual_motor_direction", "التآزر البصري واتجاه القراءة", {"التآزر البصري الحركي واتجاه القراءة"}),
        ("letter_reading", "قراءة الحروف", {"قراءة الحروف"}),
        ("syllable_reading", "قراءة المقاطع", {"قراءة المقاطع"}),
    ],
    2: [
        ("short_vowels", "الحركات القصيرة", {"تمييز الحركات", "الحركات", "الحركات القصيرة"}),
        ("long_vowels", "المد", {"تمييز المد", "المد"}),
        ("syllable_blending", "الدمج المقطعي", {"الدمج المقطعي", "دمج مقطعين", "الدمج"}),
        ("word_building", "بناء الكلمة", {"تكوين كلمة من الحروف", "بناء كلمة", "تكوين الكلمات"}),
        ("letter_order", "ترتيب حروف الكلمة", {"ترتيب الحروف", "ترتيب حروف"}),
        ("word_completion", "إكمال الكلمة", {"الإكمال", "حرف ناقص", "إكمال الكلمة"}),
        ("word_image_comprehension", "مطابقة الكلمة بالصورة", {"فهم الكلمة المكتوبة", "كلمة وصورة", "فهم المفردة"}),
        ("auditory_word_discrimination", "تمييز الكلمة سمعيًا", {"تمييز الكلمة سمعيًا", "كلمة مسموعة", "تمييز كلمة مسموعة", "التمييز السمعي"}),
        ("syllable_reading", "قراءة المقاطع", {"قراءة المقاطع"}),
        ("short_vowel_word_reading", "قراءة كلمات الحركات القصيرة", {"قراءة كلمة بالفتحة", "قراءة كلمات بسيطة", "قراءة الحركات القصيرة"}),
        ("sukoon_word_reading", "قراءة كلمات السكون", {"قراءة كلمة بالسكون"}),
        ("madd_word_reading", "قراءة كلمات المد", {"قراءة كلمة بالمد"}),
        ("shadda_word_reading", "قراءة كلمات الشدة", {"قراءة كلمة بالشدة", "قراءة الشدة"}),
        ("general_word_reading", "قراءة الكلمات", {"قراءة كلمة"}),
        ("tanween", "تمييز التنوين", {"تمييز التنوين"}),
        ("sentence_reading", "قراءة الجمل القصيرة", {"قراءة جمل قصيرة"}),
        ("sentence_building", "بناء الجملة", {"بناء الجملة"}),
    ],
    3: [
        ("word_accuracy", "دقة قراءة الكلمات", {"الدقة"}),
        ("meaning_units", "قراءة وحدات المعنى", {"قراءة وحدات المعنى", "وحدات المعنى"}),
        ("sentence_fluency", "طلاقة قراءة الجملة", {"الاسترسال", "قراءة جملة", "قراءة جهرية قصيرة"}),
        ("passage_fluency", "دقة وطلاقة قراءة النص", {"الدقة والطلاقة", "الطلاقة والدقة", "قراءة نص", "قراءة فقرة قصيرة"}),
        ("timed_word_fluency", "سرعة قراءة الكلمات مع الدقة", {"سرعة القراءة مع الدقة"}),
        ("timed_passage_fluency", "طلاقة قراءة الفقرة الموقوتة", {"الطلاقة"}),
        ("literal_comprehension", "الفهم المباشر", {"الفهم المباشر", "فهم مباشر", "استرجاع معلومات النص", "استرجاع معلومة", "استرجاع شخصية وفعل"}),
        ("inferential_comprehension", "الفهم الاستنتاجي", {"فهم استنتاجي", "فهم السبب", "فهم السبب والفكرة العامة"}),
        ("vocabulary", "المفردات من السياق", {"المفردات", "المفردات من السياق", "معنى كلمة"}),
        ("event_sequence", "تسلسل أحداث النص", {"ترتيب أحداث", "تسلسل النص", "فهم تسلسل النص"}),
        ("text_evidence", "الاستدلال من النص", {"الاستدلال من النص"}),
        ("sentence_building", "بناء الجملة", {"بناء الجملة"}),
        ("main_idea", "الفكرة العامة", {"الفكرة العامة"}),
    ],
}

FIELD_NAMES = {
    "المهارة": "skill_name",
    "طريقة التنفيذ في الويب": "source_method",
    "المحتوى/الجولات": "rounds",
    "الإجابة أو المعيار": "criterion",
    "ملاحظة": "note",
}

STORY_BINDINGS: dict[str, list[str]] = {
    **{f"PRE-Q{number:02d}": ["STY-01"] for number in range(24, 31)},
    **{f"POST-Q{number:02d}": ["STY-05"] for number in range(24, 31)},
    "L3-CORE-04": ["STY-02"],
    "L3-CORE-06": ["STY-03"],
    "L3-CORE-07": ["STY-03"],
    "L3-CORE-08": ["STY-04"],
    "L3-REIN-04": ["STY-06"],
}

ROUND_ASSET_BINDINGS: dict[tuple[str, int], list[str]] = {
    ("PRE-Q10", 1): ["SEQ-01", "SEQ-02", "SEQ-03"],
    ("POST-Q10", 1): ["SEQ-07", "SEQ-08", "SEQ-09"],
    ("L1-CORE-10", 1): ["SEQ-01", "SEQ-02", "SEQ-03"],
    ("L1-CORE-10", 2): ["SEQ-04", "SEQ-05", "SEQ-06"],
    ("L1-CORE-10", 3): ["SEQ-07", "SEQ-08", "SEQ-09"],
    **{("L2-CORE-10", number): [f"SEN-{number:02d}"] for number in range(1, 6)},
    **{("L3-CORE-03", number): [f"SEN-{number + 5:02d}"] for number in range(1, 6)},
    ("L3-CORE-10", 1): ["STY-03"],
    ("L3-CORE-10", 2): ["STY-02"],
    ("L3-CORE-10", 3): ["STY-04"],
    ("L3-REIN-05", 1): ["STY-03"],
    ("L3-REIN-05", 2): ["STY-05"],
    ("L3-REIN-05", 3): ["STY-02"],
}

def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def semantic_key(value: str) -> str:
    """Normalize Arabic for semantic manifest matching, never for display."""
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]", "", value)
    value = value.replace("ـ", "")
    value = re.sub(r"[^\w\u0600-\u06ff]+", "", value, flags=re.UNICODE)
    return value.casefold()


def image_semantic_key(value: str) -> str:
    key = semantic_key(value)
    return key[2:] if key.startswith("ال") else key


# Approved wording and the asset-kit labels differ in these two harmless noun
# forms.  The explicit aliases avoid fuzzy matching and remain reviewable.
IMAGE_LABEL_ALIASES = {
    image_semantic_key("موز"): "VOC-01",
    image_semantic_key("ماء"): "VOC-11",
    image_semantic_key("سمك"): "VOC-05",
    image_semantic_key("نور"): "VOC-15",
}


def stable_uuid(*parts: object) -> str:
    return str(uuid.uuid5(UUID_NAMESPACE, ":".join(str(part) for part in parts)))


def canonical_skill(level_id: int, source_name: str) -> tuple[str, str, str]:
    for skill_code, canonical_name, aliases in SKILL_TAXONOMY[level_id]:
        if source_name in aliases:
            return skill_code, stable_uuid("skill", level_id, skill_code), canonical_name
    raise ValueError(f"Unmapped approved skill label at level {level_id}: {source_name}")


def parse_number(title: str) -> int:
    match = re.search(r"(\d+)", title)
    if not match:
        raise ValueError(f"Heading has no numeric order: {title}")
    return int(match.group(1))


def classify_section(section: str, title: str) -> tuple[str, int, int, str]:
    number = parse_number(title)
    if section.startswith("8."):
        level_id = 1 if number <= 10 else 2 if number <= 22 else 3
        return "pretest_question", level_id, number, f"PRE-Q{number:02d}"
    if section.startswith("12."):
        level_id = 1 if number <= 10 else 2 if number <= 22 else 3
        return "posttest_question", level_id, number, f"POST-Q{number:02d}"

    section_level = {
        "9.": 1,
        "10.": 2,
        "11.": 3,
    }
    prefix = section.split(maxsplit=1)[0]
    if prefix not in section_level:
        raise ValueError(f"Unsupported content section: {section}")
    level_id = section_level[prefix]
    if title.startswith("النشاط الأساسي"):
        return "core_activity", level_id, number, f"L{level_id}-CORE-{number:02d}"
    if title.startswith("تقوية"):
        return "reinforcement_activity", level_id, number, f"L{level_id}-REIN-{number:02d}"
    raise ValueError(f"Unsupported content heading: {title}")


def classify_interaction(method: str) -> str:
    normalized = semantic_key(method)
    if ("وقت" in method or re.search(r"\d+\s*ثانية", method)) and ("يقرأ" in method or "تسجيل" in method):
        return "timed_read_aloud"
    if "تسجيل" in method or "يسجل" in method:
        return "read_aloud"
    if "تختفي" in method:
        return "memory_sequence"
    if "نقاطًا مرقمة" in method or "نقاطا مرقمة" in method:
        return "path_sequence"
    if "حروف عشوائية" in method or "النقر على الحروف" in method:
        return "build_word"
    if "بالترتيب" in method or "ترتيبها" in method or "ترتيب الحدث" in method:
        return "sequence"
    if "صورتين" in method:
        return "listen_choose_many" if "يسمع" in method else "choose_many"
    if "اختيار صورة" in method or "يختار صورة" in method or "ثلاث صور" in method:
        return "listen_choose_image" if ("سماع" in method or "يسمع" in method) else "choose_image"
    if "سماع" in method or "يسمع" in method:
        return "listen_choose_one"
    if any(
        token in method
        for token in ("اختيار", "يختار", "يظهر حرف", "يظهر عنصر", "خياران", "ثلاثة عناوين")
    ):
        return "choose_one"
    raise ValueError(f"Unknown interaction method: {method} ({normalized})")


def parse_entries(markdown: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    section = ""
    current: dict[str, Any] | None = None
    active_field: str | None = None

    def finish_current() -> None:
        nonlocal current
        if current is not None:
            entries.append(current)
            current = None

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if line.startswith("# "):
            finish_current()
            section = line[2:].strip()
            active_field = None
            continue
        if line.startswith("## "):
            finish_current()
            active_field = None
            continue
        if line.startswith("### "):
            finish_current()
            title = line[4:].strip()
            if title.startswith(("السؤال", "النشاط الأساسي", "تقوية")):
                current = {
                    "section": section,
                    "title": title,
                    "skill_name": "",
                    "source_method": "",
                    "rounds": [],
                    "criterion": "",
                    "note": "",
                }
            active_field = None
            continue
        if current is None:
            continue

        field_match = re.match(
            r"\*\*(المهارة|طريقة التنفيذ في الويب|المحتوى/الجولات|الإجابة أو المعيار|ملاحظة):\*\*\s*(.*)",
            line,
        )
        if field_match:
            active_field = FIELD_NAMES[field_match.group(1)]
            value = field_match.group(2).strip()
            if active_field == "rounds":
                if value:
                    current[active_field].append(value)
            else:
                current[active_field] = value
            continue

        if not line:
            continue
        if active_field == "rounds" and line.startswith("- "):
            current[active_field].append(line[2:].strip())
        elif active_field == "rounds" and line.startswith(">") and current[active_field]:
            current[active_field][-1] += " " + line[1:].strip()
        elif active_field in {"skill_name", "source_method", "criterion", "note"}:
            continuation = line[1:].strip() if line.startswith(">") else line
            if not continuation.startswith("**"):
                current[active_field] = f"{current[active_field]} {continuation}".strip()

    finish_current()
    return entries


def load_audio_index() -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    by_id: dict[str, dict[str, str]] = {}
    by_text: dict[str, dict[str, str]] = {}
    with AUDIO_MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            by_id[row["id"]] = row
            for field in ("text_ar", "spoken_input"):
                by_text.setdefault(semantic_key(row[field]), row)
    return by_id, by_text


def load_image_index() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    data = json.loads(IMAGE_MAP.read_text(encoding="utf-8"))
    by_id = {asset["id"]: asset for asset in data["assets"]}
    by_label = {image_semantic_key(asset["label_ar"]): asset for asset in data["assets"]}
    return by_id, by_label


def extract_quoted_target(text: str) -> str | None:
    match = re.search(r"«([^»]+)»", text)
    return match.group(1).strip() if match else None


def audio_targets(item: dict[str, Any], round_text: str) -> list[str]:
    interaction = item["interaction_type"]
    if not interaction.startswith("listen_"):
        return []
    if "كلمتين" in item["source_method"]:
        prefix = round_text.split(":", 1)[0]
        return [part.strip() for part in prefix.split("/") if part.strip()]
    quoted = extract_quoted_target(round_text)
    if quoted:
        return [quoted]
    prefix = re.split(r"[:؛]", round_text, maxsplit=1)[0].strip()
    return [prefix] if prefix else []


def image_targets(item: dict[str, Any], round_text: str) -> list[str]:
    interaction = item["interaction_type"]
    if interaction not in {
        "choose_image",
        "listen_choose_image",
        "choose_many",
        "listen_choose_many",
        "memory_sequence",
        "build_word",
    }:
        return []

    if interaction == "build_word":
        image_word = re.search(r"صورة\s+([^؛.]+)", round_text)
        if image_word:
            return [image_word.group(1).strip()]
        return [round_text.split(":", 1)[0].strip()]

    images_match = re.search(r"الصور:\s*(.+?)(?:\.|$)", round_text)
    if images_match:
        return [part.strip() for part in images_match.group(1).split("،") if part.strip()]
    if interaction == "memory_sequence":
        return [part.strip() for part in round_text.split("،") if part.strip()]
    if interaction == "choose_image" and "؛" in round_text:
        return [part.strip() for part in round_text.split("؛", 1)[1].split("،") if part.strip()]
    if ":" in round_text:
        suffix = round_text.split(":", 1)[1]
        return [part.strip() for part in re.split(r"[،/]", suffix) if part.strip()]
    image_word = re.search(r"صورة\s+([^؛.]+)", round_text)
    if image_word:
        return [image_word.group(1).strip()]
    return [round_text.strip(" .")]


def media_ref(asset: dict[str, Any], asset_type: str, usage: str, semantic_text: str) -> dict[str, str]:
    return {
        "asset_id": asset["id"],
        "asset_type": asset_type,
        "usage": usage,
        "semantic_text": semantic_text,
    }


def missing_media(asset_type: str, usage: str, semantic_text: str) -> dict[str, str]:
    return {
        "asset_type": asset_type,
        "usage": usage,
        "semantic_text": semantic_text,
        "status": "declared_missing",
        "reason": "No semantically matching approved asset exists in the current V1 manifest.",
        "impact": "The round must not be activated until an approved asset release supplies this target.",
    }


def attach_round_media(
    item: dict[str, Any],
    round_number: int,
    round_text: str,
    audio_by_text: dict[str, dict[str, str]],
    image_by_id: dict[str, dict[str, Any]],
    image_by_label: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    refs: list[dict[str, str]] = []
    gaps: list[dict[str, str]] = []

    for target in audio_targets(item, round_text):
        asset = audio_by_text.get(semantic_key(target))
        if asset:
            refs.append(media_ref(asset, "audio", "prompt", target))
        else:
            gaps.append(missing_media("audio", "prompt", target))

    for target in image_targets(item, round_text):
        key = image_semantic_key(target)
        alias_id = IMAGE_LABEL_ALIASES.get(key)
        asset = image_by_id.get(alias_id) if alias_id else image_by_label.get(key)
        if asset:
            refs.append(media_ref(asset, "image", "choice", target))
        else:
            gaps.append(missing_media("image", "choice", target))

    for asset_id in ROUND_ASSET_BINDINGS.get((item["canonical_id"], round_number), []):
        asset = image_by_id[asset_id]
        refs.append(media_ref(asset, "image", "illustration", asset["label_ar"]))

    unique_refs = {f"{ref['asset_type']}:{ref['asset_id']}:{ref['usage']}": ref for ref in refs}
    unique_gaps = {
        f"{gap['asset_type']}:{semantic_key(gap['semantic_text'])}:{gap['usage']}": gap
        for gap in gaps
    }
    return list(unique_refs.values()), list(unique_gaps.values())


def build_catalog() -> dict[str, Any]:
    original_hash = file_sha256(ORIGINAL_SOURCE)
    derived_hash = file_sha256(DERIVED_SOURCE)
    entries = parse_entries(DERIVED_SOURCE.read_text(encoding="utf-8"))
    audio_by_id, audio_by_text = load_audio_index()
    image_by_id, image_by_label = load_image_index()

    items: list[dict[str, Any]] = []
    skills: dict[str, dict[str, Any]] = {}
    for entry in entries:
        kind, level_id, order_index, canonical_id = classify_section(entry["section"], entry["title"])
        interaction_type = classify_interaction(entry["source_method"])
        source_skill_name = entry["skill_name"]
        skill_code, skill_id, skill_name = canonical_skill(level_id, source_skill_name)
        skills.setdefault(
            skill_id,
            {
                "skill_id": skill_id,
                "skill_code": skill_code,
                "level_id": level_id,
                "name": skill_name,
            },
        )

        item: dict[str, Any] = {
            "canonical_id": canonical_id,
            "stable_key": stable_uuid("item", canonical_id),
            "kind": kind,
            "level_id": level_id,
            "order_index": order_index,
            "title": entry["title"],
            "skill_id": skill_id,
            "skill_name": skill_name,
            "source_skill_name": source_skill_name,
            "interaction_type": interaction_type,
            "source_method": entry["source_method"],
            "criterion": entry["criterion"] or None,
            "note": entry["note"] or None,
            "item_assets": [],
            "rounds": [],
        }

        for asset_id in STORY_BINDINGS.get(canonical_id, []):
            asset = image_by_id[asset_id]
            item["item_assets"].append(media_ref(asset, "image", "passage_context", asset["label_ar"]))

        for round_number, source_text in enumerate(entry["rounds"], start=1):
            refs, gaps = attach_round_media(
                item,
                round_number,
                source_text,
                audio_by_text,
                image_by_id,
                image_by_label,
            )
            item["rounds"].append(
                {
                    "round_id": f"{canonical_id}-R{round_number:02d}",
                    "order_index": round_number,
                    "source_text": source_text,
                    "media": refs,
                    "media_gaps": gaps,
                }
            )

        item_without_checksum = dict(item)
        item["checksum"] = hashlib.sha256(canonical_json(item_without_checksum).encode("utf-8")).hexdigest()
        items.append(item)

    kind_counts = Counter(item["kind"] for item in items)
    level_activity_counts: dict[str, dict[str, int]] = {}
    for level_id in LEVEL_NAMES:
        level_activity_counts[str(level_id)] = {
            "core": sum(1 for item in items if item["level_id"] == level_id and item["kind"] == "core_activity"),
            "reinforcement": sum(
                1 for item in items if item["level_id"] == level_id and item["kind"] == "reinforcement_activity"
            ),
        }

    media_gaps = [
        {
            "item_id": item["canonical_id"],
            "round_id": round_data["round_id"],
            **gap,
        }
        for item in items
        for round_data in item["rounds"]
        for gap in round_data["media_gaps"]
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "catalog_version": CATALOG_VERSION,
        "language": "ar",
        "direction": "rtl",
        "source": {
            "authority": "client_approved_docx",
            "original_path": str(ORIGINAL_SOURCE.relative_to(REPO_ROOT)).replace("\\", "/"),
            "original_sha256": original_hash,
            "derived_path": str(DERIVED_SOURCE.relative_to(REPO_ROOT)).replace("\\", "/"),
            "derived_sha256": derived_hash,
        },
        "constraints": {
            "pretest_questions": 30,
            "posttest_questions": 30,
            "assessment_level_distribution": {"1": 10, "2": 12, "3": 8},
            "core_activities_per_level": 10,
            "reinforcement_activities_per_level": 5,
            "allowed_interactions": sorted(INTERACTIONS),
            "one_skill_per_item": True,
            "one_interaction_per_item": True,
        },
        "summary": {
            "item_count": len(items),
            "skill_count": len(skills),
            "kind_counts": dict(sorted(kind_counts.items())),
            "activity_counts_by_level": level_activity_counts,
            "declared_media_gap_count": len(media_gaps),
        },
        "levels": [
            {
                "level_id": level_id,
                "name": name,
                "core_activity_ids": [
                    item["canonical_id"]
                    for item in items
                    if item["level_id"] == level_id and item["kind"] == "core_activity"
                ],
                "reinforcement_activity_ids": [
                    item["canonical_id"]
                    for item in items
                    if item["level_id"] == level_id and item["kind"] == "reinforcement_activity"
                ],
            }
            for level_id, name in LEVEL_NAMES.items()
        ],
        "skills": sorted(skills.values(), key=lambda skill: (skill["level_id"], skill["name"])),
        "media_gaps": media_gaps,
        "items": items,
        "manifest_inventory": {
            "audio_asset_ids": sorted(audio_by_id),
            "image_asset_ids": sorted(image_by_id),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if catalog.json differs from generated output")
    args = parser.parse_args()
    catalog = build_catalog()
    rendered = json.dumps(catalog, ensure_ascii=False, indent=2) + "\n"

    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != rendered:
            print("catalog.json is stale; run compile_catalog.py")
            return 1
        print("catalog.json matches the approved source")
        return 0

    OUTPUT.write_text(rendered, encoding="utf-8")
    print(
        f"Wrote {len(catalog['items'])} items, {len(catalog['skills'])} skills, "
        f"and {len(catalog['media_gaps'])} declared media gaps to {OUTPUT}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
