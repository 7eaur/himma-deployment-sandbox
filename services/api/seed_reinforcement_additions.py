"""Idempotently seed the approved M03 reinforcement extension.

The original 105-item client catalog remains immutable.  The maintenance-
approved 18 micro-reinforcements live in a separate versioned JSON catalog and
are inserted as an additive content release.  This module never rewrites the
original catalog rows.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from db.database import SessionLocal
from db.models import ContentItem, ContentKind, ContentOption, ContentStep, Skill


ROOT = Path(__file__).resolve().parents[2]
ADDITIONS_PATH = ROOT / "packages" / "content" / "src" / "reinforcement_additions_v1.json"
MAP_PATH = ROOT / "packages" / "content" / "src" / "reinforcement_skill_map_v1.json"
CATALOG_VERSION = "HIMMA-REINFORCEMENT-ADD-1.0"

PRIMARY_SKILL_BY_ITEM = {
    "L1-REIN-06": "sound_symbol_mapping",
    "L1-REIN-07": "letter_form_recognition",
    "L1-REIN-08": "final_sound_isolation",
    "L1-REIN-09": "print_concepts",
    "L1-REIN-10": "visual_memory",
    "L1-REIN-11": "visual_motor_direction",
    "L1-REIN-12": "logical_sequence",
    "L2-REIN-06": "short_vowels",
    "L2-REIN-07": "syllable_reading",
    "L2-REIN-08": "long_vowels",
    "L2-REIN-09": "shadda_word_reading",
    "L2-REIN-10": "tanween",
    "L2-REIN-11": "sentence_reading",
    "L3-REIN-06": "word_accuracy",
    "L3-REIN-07": "timed_word_fluency",
    "L3-REIN-08": "timed_passage_fluency",
    "L3-REIN-09": "vocabulary",
    "L3-REIN-10": "event_sequence",
}


def _load() -> dict[str, Any]:
    data = json.loads(ADDITIONS_PATH.read_text(encoding="utf-8"))
    if data.get("catalog_version") != CATALOG_VERSION:
        raise RuntimeError("Unexpected reinforcement extension version")
    items = data.get("items")
    if not isinstance(items, list) or len(items) != 18:
        raise RuntimeError("M03 reinforcement extension must contain exactly 18 items")
    return data


def extension_stable_key(canonical_id: str) -> str:
    return f"himma:reinforcement-addition:{canonical_id.lower()}"


def extension_stable_keys() -> set[str]:
    return {extension_stable_key(item["canonical_id"]) for item in _load()["items"]}


def _canonical_order(canonical_id: str) -> int:
    try:
        return int(canonical_id.rsplit("-", 1)[1])
    except (IndexError, ValueError) as exc:
        raise RuntimeError(f"Invalid reinforcement canonical id: {canonical_id}") from exc


def _checksum(item: dict[str, Any]) -> str:
    raw = json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _runtime_interaction(canonical: str) -> str:
    return "read_aloud" if canonical in {"read_aloud", "timed_read_aloud"} else "multiple_choice"


def _round_prompt(item: dict[str, Any], round_data: dict[str, Any], index: int) -> str:
    if round_data.get("prompt"):
        return str(round_data["prompt"])
    if round_data.get("audio_text"):
        return "استمع جيدًا ثم اختر الإجابة الصحيحة."
    if round_data.get("text"):
        return str(round_data["text"])
    if round_data.get("sequence"):
        return "رتّب العناصر بالترتيب الصحيح."
    if round_data.get("path"):
        return "اتبع المسار من اليمين إلى اليسار بالترتيب."
    if round_data.get("expected_reading"):
        return "اقرأ النص الظاهر بصوت واضح."
    return f"{item['title']} — الجولة {index}"


def _expected_reading(round_data: dict[str, Any]) -> str | None:
    value = round_data.get("expected_reading")
    if value is None:
        return None
    if isinstance(value, list):
        return " ".join(str(part) for part in value)
    return str(value)


def _sequence_values(round_data: dict[str, Any]) -> list[str]:
    if isinstance(round_data.get("sequence"), list):
        return [str(value) for value in round_data["sequence"]]
    if isinstance(round_data.get("path"), str):
        count = int(round_data["path"].split("_", 1)[0])
        return [str(index) for index in range(1, count + 1)]
    return []


def _options(item: dict[str, Any], round_data: dict[str, Any]) -> list[tuple[str, bool]]:
    interaction = item["interaction"]
    if interaction in {"read_aloud", "timed_read_aloud"}:
        return []
    if interaction in {"sequence", "memory_sequence", "path_sequence"}:
        return [(value, index == 0) for index, value in enumerate(_sequence_values(round_data))]

    values = [str(value) for value in round_data.get("options", [])]
    answer = str(round_data.get("answer", values[0] if values else ""))
    return [(value, value == answer) for value in values]


def _representative_skill(db: Session, item: dict[str, Any]) -> Skill:
    canonical_id = item["canonical_id"]
    skill_code = PRIMARY_SKILL_BY_ITEM.get(canonical_id)
    if skill_code is None:
        raise RuntimeError(f"No primary skill configured for {canonical_id}")
    skill = db.query(Skill).filter(
        Skill.canonical_skill_id == skill_code,
        Skill.level_id == int(item["level"]),
    ).first()
    if not skill:
        raise RuntimeError(f"Primary skill {skill_code} not seeded for {canonical_id}")
    return skill


def run_seed() -> int:
    data = _load()
    db: Session = SessionLocal()
    created = 0
    try:
        for item in data["items"]:
            stable_key = extension_stable_key(item["canonical_id"])
            order_index = _canonical_order(item["canonical_id"])
            checksum = _checksum(item)
            existing = db.query(ContentItem).filter(ContentItem.stable_key == stable_key).first()
            if existing:
                if existing.checksum != checksum:
                    raise RuntimeError(
                        f"Versioned reinforcement {item['canonical_id']} changed; create a new content version"
                    )
                # Ordering is operational metadata, not academic content; repair
                # an early M03 seed that used a global enumerate order.
                if existing.order_index != order_index:
                    existing.order_index = order_index
                continue

            skill = _representative_skill(db, item)
            template_data = {
                "canonical_id": item["canonical_id"],
                "title": item["title"],
                "canonical_interaction_type": item["interaction"],
                "target_skill_family": item["target_skill_family"],
                "target_skills": item["target_skills"],
                "success_threshold": item["success_threshold"],
                "verification_required": item["verification_required"],
                "catalog_version": CATALOG_VERSION,
                "maintenance_addition": True,
                "media": item.get("media", {}),
                "ui": item.get("ui", {}),
            }
            db_item = ContentItem(
                stable_key=stable_key,
                kind=ContentKind.reinforcement_activity,
                level_id=int(item["level"]),
                skill_id=skill.id,
                interaction_type=_runtime_interaction(item["interaction"]),
                order_index=order_index,
                version=CATALOG_VERSION,
                status="approved",
                checksum=checksum,
                template_data=template_data,
            )
            db.add(db_item)
            db.flush()

            for round_index, round_data in enumerate(item["rounds"], start=1):
                step = ContentStep(
                    item_id=db_item.id,
                    order_index=round_index,
                    prompt_text=_round_prompt(item, round_data, round_index),
                    expected_reading_text=_expected_reading(round_data),
                )
                db.add(step)
                db.flush()
                for option_index, (text, is_correct) in enumerate(_options(item, round_data), start=1):
                    db.add(ContentOption(
                        step_id=step.id,
                        text=text,
                        is_correct=is_correct,
                        order_index=option_index,
                    ))
            created += 1

        db.commit()
        print(f"Created {created} versioned M03 reinforcement additions.")
        return created
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
