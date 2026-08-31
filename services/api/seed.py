"""Idempotently seed the database from the approved Himma content catalog.

The catalog preserves source rounds and richer interaction types. The current
assessment runner supports choice and read-aloud only, so non-audio templates
are projected to the existing choice contract while their canonical type and
full approved source remain in ``template_data`` for later template slices.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.database import SQLALCHEMY_DATABASE_URL
from db.models import (
    Attempt,
    ContentAssetLink,
    ContentItem,
    ContentKind,
    ContentOption,
    ContentStep,
    ScoringPolicy,
    ScoringRule,
    Skill,
)


engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

CATALOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "packages",
    "content",
    "src",
    "catalog.json",
)

READING_INTERACTIONS = {"read_aloud", "timed_read_aloud"}
SEQUENCE_INTERACTIONS = {"sequence", "memory_sequence", "path_sequence", "build_word"}


def _semantic_key(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]", "", value)
    value = value.replace("ـ", "")
    value = re.sub(r"[^\w\u0600-\u06ff]+", "", value, flags=re.UNICODE)
    if value.startswith("ال"):
        value = value[2:]
    return value.casefold()


def _clean_parts(value: str) -> list[str]:
    return [part.strip(" .") for part in re.split(r"[،/]", value) if part.strip(" .")]


def _extract_options(item: dict[str, Any], source_text: str) -> list[str]:
    interaction = item["interaction_type"]
    for label in ("الخيارات:", "الصور:"):
        if label in source_text:
            return _clean_parts(source_text.split(label, 1)[1].strip())

    if source_text.startswith("العناصر:"):
        values = source_text.split("التعليمات:", 1)[0].split(":", 1)[1]
        return _clean_parts(values)

    for label in ("المقاطع:", "الحروف:"):
        if label in source_text:
            suffix = source_text.split(label, 1)[1]
            suffix = re.split(r"\.\s*(?:كوّن|كون)", suffix, maxsplit=1)[0]
            return _clean_parts(suffix)

    if interaction in SEQUENCE_INTERACTIONS:
        if ":" in source_text:
            prefix, suffix = source_text.split(":", 1)
            if "=" in prefix or interaction == "build_word":
                return _clean_parts(suffix)
        if "؛" in source_text:
            return [part.strip(" .") for part in source_text.split("؛") if part.strip(" .")]
        if "+" in source_text:
            return [part.strip() for part in source_text.split("=", 1)[0].split("+") if part.strip()]
        return _clean_parts(source_text)

    if "؛" in source_text:
        return _clean_parts(source_text.split("؛", 1)[1])
    if "؟" in source_text:
        return _clean_parts(source_text.split("؟", 1)[1])
    if ". " in source_text and item["interaction_type"].startswith("listen_"):
        return _clean_parts(source_text.split(". ", 1)[1])
    if ":" in source_text:
        prefix, suffix = source_text.split(":", 1)
        if "/" in suffix or "،" in suffix:
            return _clean_parts(suffix)
        if "/" in prefix:
            return ["نفسه", "مختلفان"]
        if suffix.strip():
            if item["skill_name"] == "مفاهيم المادة المطبوعة":
                return ["حرف", "كلمة", "جملة"]
            return [suffix.strip(" .")]
    if "=" in source_text:
        return [source_text.split("=", 1)[1].strip(" .")]
    return [source_text.strip(" .")]


def _question_answer(item: dict[str, Any]) -> str | None:
    criterion = item.get("criterion")
    if not criterion or criterion.startswith("مطابقة") or "الترتيب" in criterion:
        return None
    if criterion in {
        "الدقة والاسترسال",
        "تحليل الكلمات والوقت",
        "الكلمات الصحيحة والحذف والإضافة والاستبدال والوقت",
    }:
        return None
    return criterion


def _round_answer(item: dict[str, Any], source_text: str, options: list[str]) -> str | None:
    question_answer = _question_answer(item)
    if question_answer:
        return question_answer
    if not options:
        return None
    if item["interaction_type"] in SEQUENCE_INTERACTIONS:
        return options[0]
    if ":" in source_text:
        prefix, suffix = source_text.split(":", 1)
        if "/" in prefix:
            return suffix.strip(" .")
        if len(options) > 1:
            return prefix.strip(" .")
        return suffix.strip(" .")
    if "=" in source_text:
        return source_text.split("=", 1)[1].strip(" .")
    return options[0]


def _correct_index(answer: str | None, options: list[str]) -> int:
    if not options:
        return -1
    if not answer:
        return 0
    answer_key = _semantic_key(answer)
    option_keys = [_semantic_key(option) for option in options]
    for index, option_key in enumerate(option_keys):
        if option_key == answer_key or option_key in answer_key or answer_key in option_key:
            return index
    return max(
        range(len(options)),
        key=lambda index: SequenceMatcher(None, answer_key, option_keys[index]).ratio(),
    )


def _expected_reading_text(source_text: str) -> str:
    return re.sub(r"^اقرأ(?:\s+النص\s+الآتي)?\s*:\s*", "", source_text).strip()


def _step_payload(item: dict[str, Any], round_data: dict[str, Any]) -> dict[str, Any]:
    source_text = round_data["source_text"]
    if item["interaction_type"] in READING_INTERACTIONS:
        return {
            "prompt_text": "اقرأ النص الظاهر بصوت واضح.",
            "expected_reading_text": _expected_reading_text(source_text),
            "options": [],
        }

    options = _extract_options(item, source_text)
    answer = _round_answer(item, source_text, options)
    correct_index = _correct_index(answer, options)
    return {
        "prompt_text": source_text,
        "expected_reading_text": None,
        "options": [
            {
                "text": option,
                "is_correct": index == correct_index,
                "order_index": index + 1,
            }
            for index, option in enumerate(options)
        ],
    }


def _catalog_items(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    if catalog.get("schema_version") != 1:
        raise RuntimeError("Unsupported content catalog schema")
    items = catalog.get("items")
    if not isinstance(items, list) or len(items) != 105:
        raise RuntimeError("Approved content catalog must contain exactly 105 items")
    return items


def run_seed() -> None:
    if not os.path.exists(CATALOG_PATH):
        print(f"Catalog not found at {CATALOG_PATH}")
        sys.exit(1)

    with open(CATALOG_PATH, "r", encoding="utf-8") as handle:
        catalog = json.load(handle)
    items = _catalog_items(catalog)

    db: Session = SessionLocal()
    try:
        catalog_keys = {item["stable_key"] for item in items}
        existing_items = db.query(ContentItem).all()
        legacy_keys = {item.stable_key for item in existing_items} - catalog_keys
        if legacy_keys:
            raise RuntimeError(
                "Database contains a legacy content catalog. Refusing to mix old and approved "
                "content; run the reviewed B01 data reconciliation before reseeding."
            )

        print(f"Starting approved catalog seed of {len(items)} items...")
        skills_created = 0
        for skill_data in catalog["skills"]:
            skill = db.query(Skill).filter(Skill.skill_key == skill_data["skill_id"]).first()
            if not skill:
                skill = Skill(
                    skill_key=skill_data["skill_id"],
                    canonical_skill_id=skill_data["skill_code"],
                    name=skill_data["name"],
                    description=skill_data["name"],
                    level_id=skill_data["level_id"],
                )
                db.add(skill)
                skills_created += 1
            else:
                skill.canonical_skill_id = skill_data["skill_code"]
                skill.name = skill_data["name"]
                skill.description = skill_data["name"]
                skill.level_id = skill_data["level_id"]
        db.commit()
        print(f"Created {skills_created} new skills.")

        skills_map = {skill.skill_key: skill.id for skill in db.query(Skill).all()}
        db_items: dict[str, ContentItem] = {}
        items_created = 0
        for item_data in items:
            stable_key = item_data["stable_key"]
            existing = db.query(ContentItem).filter(ContentItem.stable_key == stable_key).first()
            if existing:
                if existing.checksum != item_data["checksum"]:
                    has_attempt = db.query(Attempt).filter(Attempt.item_id == existing.id).first()
                    suffix = " and has attempts" if has_attempt else ""
                    raise RuntimeError(
                        f"Approved content {item_data['canonical_id']} changed{suffix}; "
                        "a reviewed versioned data migration is required."
                    )
                db_items[stable_key] = existing
                continue

            runtime_interaction = (
                "read_aloud" if item_data["interaction_type"] in READING_INTERACTIONS else "multiple_choice"
            )
            template_data = {
                "canonical_id": item_data["canonical_id"],
                "title": item_data["title"],
                "canonical_interaction_type": item_data["interaction_type"],
                "source_skill_name": item_data["source_skill_name"],
                "source_method": item_data["source_method"],
                "criterion": item_data["criterion"],
                "note": item_data["note"],
                "item_assets": item_data["item_assets"],
                "media_gaps": [
                    gap for round_data in item_data["rounds"] for gap in round_data["media_gaps"]
                ],
                "catalog_version": catalog["catalog_version"],
            }
            new_item = ContentItem(
                stable_key=stable_key,
                kind=ContentKind(item_data["kind"]),
                level_id=item_data["level_id"],
                skill_id=skills_map[item_data["skill_id"]],
                interaction_type=runtime_interaction,
                order_index=item_data["order_index"],
                version=catalog["catalog_version"],
                status="approved",
                checksum=item_data["checksum"],
                template_data=template_data,
            )
            db.add(new_item)
            db.flush()

            for round_data in item_data["rounds"]:
                payload = _step_payload(item_data, round_data)
                step = ContentStep(
                    item_id=new_item.id,
                    order_index=round_data["order_index"],
                    prompt_text=payload["prompt_text"],
                    expected_reading_text=payload["expected_reading_text"],
                )
                db.add(step)
                db.flush()
                for option in payload["options"]:
                    db.add(ContentOption(step_id=step.id, **option))
                for media in round_data["media"]:
                    db.add(
                        ContentAssetLink(
                            step_id=step.id,
                            manifest_asset_id=media["asset_id"],
                            asset_type=media["asset_type"],
                            usage_context=media["usage"],
                        )
                    )
            for media in item_data["item_assets"]:
                db.add(
                    ContentAssetLink(
                        item_id=new_item.id,
                        manifest_asset_id=media["asset_id"],
                        asset_type=media["asset_type"],
                        usage_context=media["usage"],
                    )
                )

            db_items[stable_key] = new_item
            items_created += 1
        db.commit()
        print(f"Created {items_created} new content items.")

        policy_version = "SCORING_POLICY_V1"
        policy = db.query(ScoringPolicy).filter(ScoringPolicy.version == policy_version).first()
        if not policy:
            policy = ScoringPolicy(
                version=policy_version,
                status="approved",
                approved_by=None,
                approved_at=datetime.datetime.strptime("2026-08-11", "%Y-%m-%d").replace(
                    tzinfo=datetime.timezone.utc
                ),
                checksum="seeded_by_script",
            )
            db.add(policy)
            db.flush()
            for db_item in db_items.values():
                if db_item.kind in {ContentKind.pretest_question, ContentKind.posttest_question}:
                    db.add(
                        ScoringRule(
                            policy_id=policy.id,
                            item_id=db_item.id,
                            max_raw_score=1.0,
                            rubric=(
                                "V1: 1 point for correct non-audio. For audio: "
                                "max(0, 1 - (errors/target_units))."
                            ),
                        )
                    )
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
