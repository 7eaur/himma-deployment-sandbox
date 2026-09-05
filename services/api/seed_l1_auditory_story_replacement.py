"""Seed the approved L1 auditory-comprehension replacements from one source.

The authoritative source lives in packages/content/src/l1_auditory_comprehension_v1.json.
This seed projects that source into the normalized content tables only. DB runtime
projection is owned by seed_db_runtime_contract.py; there is deliberately no
post-projection patch step here.

The retired visual-motor activity was the only baseline owner of its level-1
skill row. Because the approved replacement changes the academic construct, the
same durable Skill row is reconciled in-place to the new construct instead of
creating a 45th canonical skill or deleting historical foreign-key evidence.
"""
from __future__ import annotations

import json
from pathlib import Path

from db.database import SessionLocal
from db.models import ContentAssetLink, ContentItem, ContentOption, Skill

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "packages" / "content" / "src" / "l1_auditory_comprehension_v1.json"
EXPECTED_VERSION = "HIMMA-L1-AUDITORY-COMPREHENSION-2026-09-02"
RETIRED_SKILL_CODE = "visual_motor_direction"
SKILL_CODE = "auditory_literal_comprehension"
SKILL_NAME = "الفهم السمعي المباشر"


def _load_source() -> tuple[str, dict[str, dict]]:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    version = str(payload.get("version") or "")
    if version != EXPECTED_VERSION:
        raise RuntimeError(f"Unexpected auditory source version: {version!r}")
    items = {str(item["canonical_id"]): item for item in payload.get("items", [])}
    if set(items) != {"L1-CORE-09", "L1-REIN-11"}:
        raise RuntimeError(f"Unexpected auditory source items: {sorted(items)}")
    return version, items


VERSION, STORIES = _load_source()


def _find_item(db, canonical: str) -> ContentItem:
    for item in db.query(ContentItem).all():
        if item.stable_key == canonical or str((item.template_data or {}).get("canonical_id") or "") == canonical:
            return item
    raise RuntimeError(f"Missing auditory replacement item: {canonical}")


def _auditory_skill(db) -> Skill:
    current = db.query(Skill).filter(
        Skill.level_id == 1,
        Skill.canonical_skill_id == SKILL_CODE,
    ).first()
    if current:
        current.name = SKILL_NAME
        current.description = SKILL_NAME
        return current

    retired = db.query(Skill).filter(
        Skill.level_id == 1,
        Skill.canonical_skill_id == RETIRED_SKILL_CODE,
    ).first()
    if not retired:
        raise RuntimeError(
            "Cannot reconcile auditory-comprehension skill: retired level-1 skill row is missing"
        )
    retired.canonical_skill_id = SKILL_CODE
    retired.name = SKILL_NAME
    retired.description = SKILL_NAME
    return retired


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


def _set_story_audio(db, step, asset_id: str | None) -> None:
    for asset in list(step.assets):
        db.delete(asset)
    if asset_id:
        db.add(ContentAssetLink(
            step_id=step.id,
            manifest_asset_id=asset_id,
            asset_type="audio",
            usage_context="prompt",
        ))


def run_seed() -> int:
    db = SessionLocal()
    changed = 0
    try:
        skill = _auditory_skill(db)
        db.flush()

        for canonical, spec in STORIES.items():
            item = _find_item(db, canonical)
            steps = sorted(item.steps, key=lambda step: step.order_index)
            rounds = list(spec.get("rounds") or [])
            if len(steps) != 5 or len(rounds) != 5:
                raise RuntimeError(f"{canonical} must have exactly five rounds")

            item.skill_id = skill.id
            data = dict(item.template_data or {})
            data["title"] = spec["title"]
            data["canonical_interaction_type"] = spec["interaction_type"]
            data["auditory_story_version"] = VERSION
            data["auditory_story"] = {
                "version": VERSION,
                "skill": SKILL_NAME,
                "story_text_internal": spec["story_text_internal"],
                "audio_asset_id": spec.get("audio_asset_id"),
                "audio_status": spec.get("audio_status"),
                "student_visible_story_text": bool(spec.get("student_visible_story_text", False)),
                "rounds": rounds,
            }
            item.template_data = data

            for step, round_spec in zip(steps, rounds, strict=True):
                step.prompt_text = "قصة صوتية — النص غير معروض للطالب"
                step.expected_reading_text = None
                _set_options(db, step, list(round_spec["options"]), str(round_spec["answer"]))
                _set_story_audio(db, step, spec.get("audio_asset_id"))

            changed += 1

        db.commit()
        return changed
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print({"content_changed": run_seed(), "source_version": VERSION, "skill": SKILL_CODE})
