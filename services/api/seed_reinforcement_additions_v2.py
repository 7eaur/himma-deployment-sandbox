"""Seed the explicitly approved 2026-08-29 reinforcement gap additions.

This release is additive. It does not rewrite the immutable 105-item client
catalog or the previously accepted v1 maintenance extension.
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
ADDITIONS_PATH = ROOT / "packages" / "content" / "src" / "reinforcement_additions_v2.json"
CATALOG_VERSION = "HIMMA-REINFORCEMENT-ADD-2.0"

PRIMARY_SKILL_BY_ITEM = {
    "L3-REIN-11": "literal_comprehension",
    "L3-REIN-12": "sentence_building",
}


def _load() -> dict[str, Any]:
    data = json.loads(ADDITIONS_PATH.read_text(encoding="utf-8"))
    if data.get("catalog_version") != CATALOG_VERSION:
        raise RuntimeError("Unexpected reinforcement v2 extension version")
    items = data.get("items")
    if not isinstance(items, list) or len(items) != 2:
        raise RuntimeError("Reinforcement v2 extension must contain exactly 2 approved items")
    return data


def extension_stable_key(canonical_id: str) -> str:
    return f"himma:reinforcement-addition-v2:{canonical_id.lower()}"


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
    if round_data.get("sequence"):
        return "رتّب الكلمات لتكوين الجملة الصحيحة."
    return f"{item['title']} — الجولة {index}"


def _sequence_values(round_data: dict[str, Any]) -> list[str]:
    value = round_data.get("sequence")
    return [str(part) for part in value] if isinstance(value, list) else []


def _options(item: dict[str, Any], round_data: dict[str, Any]) -> list[tuple[str, bool]]:
    if item["interaction"] == "sequence":
        return [(value, index == 0) for index, value in enumerate(_sequence_values(round_data))]
    values = [str(value) for value in round_data.get("options", [])]
    answer = str(round_data.get("answer", values[0] if values else ""))
    return [(value, value == answer) for value in values]


def _representative_skill(db: Session, item: dict[str, Any]) -> Skill:
    skill_code = PRIMARY_SKILL_BY_ITEM[item["canonical_id"]]
    skill = db.query(Skill).filter(
        Skill.canonical_skill_id == skill_code,
        Skill.level_id == int(item["level"]),
    ).first()
    if not skill:
        raise RuntimeError(f"Primary skill {skill_code} not seeded for {item['canonical_id']}")
    return skill


def run_seed() -> int:
    data = _load()
    db: Session = SessionLocal()
    created = 0
    try:
        for item in data["items"]:
            stable_key = extension_stable_key(item["canonical_id"])
            checksum = _checksum(item)
            existing = db.query(ContentItem).filter(ContentItem.stable_key == stable_key).first()
            if existing:
                if existing.checksum != checksum:
                    raise RuntimeError(
                        f"Versioned reinforcement {item['canonical_id']} changed; create a new content version"
                    )
                continue

            skill = _representative_skill(db, item)
            db_item = ContentItem(
                stable_key=stable_key,
                kind=ContentKind.reinforcement_activity,
                level_id=int(item["level"]),
                skill_id=skill.id,
                interaction_type=_runtime_interaction(item["interaction"]),
                order_index=_canonical_order(item["canonical_id"]),
                version=CATALOG_VERSION,
                status="approved",
                checksum=checksum,
                template_data={
                    "canonical_id": item["canonical_id"],
                    "title": item["title"],
                    "canonical_interaction_type": item["interaction"],
                    "target_skill_family": item["target_skill_family"],
                    "target_skills": item["target_skills"],
                    "success_threshold": item["success_threshold"],
                    "verification_required": item["verification_required"],
                    "catalog_version": CATALOG_VERSION,
                    "maintenance_addition": True,
                    "approval_source": "explicit_user_approval_2026_08_29",
                },
            )
            db.add(db_item)
            db.flush()

            for round_index, round_data in enumerate(item["rounds"], start=1):
                step = ContentStep(
                    item_id=db_item.id,
                    order_index=round_index,
                    prompt_text=_round_prompt(item, round_data, round_index),
                    expected_reading_text=None,
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
        print(f"Created {created} versioned reinforcement v2 additions.")
        return created
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
