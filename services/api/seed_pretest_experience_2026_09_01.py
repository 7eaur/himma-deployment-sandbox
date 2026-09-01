"""Apply the 2026-09-01 user-approved pretest presentation/content contract.

This is an overlay on top of the immutable baseline catalog and Student Experience v2.
It keeps historical source text intact while projecting the exact 30-question pretest
contract into runtime fields used by the student UI.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from db.database import SessionLocal
from db.models import ContentItem


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "packages" / "content" / "src" / "pretest_experience_2026_09_01.json"
VERSION = "HIMMA-PRETEST-2026-09-01"


def _load_contract() -> list[dict[str, Any]]:
    payload = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if payload.get("version") != VERSION:
        raise RuntimeError(f"Unexpected pretest contract version: {payload.get('version')!r}")
    items = payload.get("items")
    if not isinstance(items, list) or len(items) != 30:
        raise RuntimeError("Pretest contract must contain exactly 30 items")
    expected = {f"PRE-Q{index:02d}" for index in range(1, 31)}
    actual = {str(item.get("canonical_id")) for item in items}
    if actual != expected:
        raise RuntimeError(f"Pretest canonical IDs mismatch: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")
    return items


def _criterion(contract: dict[str, Any], current: str | None) -> str | None:
    interaction = str(contract["interaction_type"])
    answer = contract.get("correct_answer")
    if interaction in {"sequence", "memory_sequence", "path_sequence", "build_word"}:
        if not isinstance(answer, list) or not answer:
            raise RuntimeError(f"{contract['canonical_id']}: ordered interaction requires an ordered correct_answer list")
        return " ثم ".join(str(part) for part in answer)
    return current


def _apply_item(item: ContentItem, contract: dict[str, Any]) -> int:
    canonical = str((item.template_data or {}).get("canonical_id") or item.stable_key)
    if item.kind != "pretest_question":
        raise RuntimeError(f"{canonical}: expected pretest_question, got {item.kind}")
    if len(item.steps) != 1:
        raise RuntimeError(f"{canonical}: expected exactly one runtime step, got {len(item.steps)}")

    changed = 0
    step = item.steps[0]
    options = sorted(step.options, key=lambda option: option.order_index)
    contract_options = [str(value) for value in contract.get("options", [])]
    if len(options) != len(contract_options):
        raise RuntimeError(f"{canonical}: option count mismatch runtime={len(options)} contract={len(contract_options)}")

    interaction = str(contract["interaction_type"])
    if item.interaction_type != interaction:
        item.interaction_type = interaction
        changed += 1

    stimulus = dict(contract.get("stimulus") or {})
    stimulus_kind = str(stimulus.get("kind") or "none")
    stimulus_text = str(stimulus.get("text") or "")
    prompt_text = stimulus_text if stimulus_kind in {"text", "reading"} else ""
    if step.prompt_text != prompt_text:
        step.prompt_text = prompt_text
        changed += 1

    expected_reading = stimulus_text if stimulus_kind == "reading" else None
    if step.expected_reading_text != expected_reading:
        step.expected_reading_text = expected_reading
        changed += 1

    answer = contract.get("correct_answer")
    answer_set = {str(value) for value in answer} if isinstance(answer, list) else {str(answer)}
    for index, option in enumerate(options):
        new_text = contract_options[index]
        if option.text != new_text:
            option.text = new_text
            changed += 1
        should_be_correct = new_text in answer_set
        if bool(option.is_correct) != should_be_correct:
            option.is_correct = should_be_correct
            changed += 1
        if option.order_index != index + 1:
            option.order_index = index + 1
            changed += 1

    data = dict(item.template_data or {})
    new_data = dict(data)
    new_data["title"] = str(contract["skill"])
    new_data["canonical_interaction_type"] = interaction
    new_data["pretest_experience_version"] = VERSION
    new_data["pretest_experience"] = {
        "version": VERSION,
        "question_number": int(contract["question_number"]),
        "section": str(contract["section"]),
        "skill": str(contract["skill"]),
        "encouragement": str(contract["encouragement"]),
        "question_text": str(contract["question_text"]),
        "instruction_text": str(contract["instruction_text"]),
        "stimulus": stimulus,
        "interaction_type": interaction,
        "media_semantics": contract.get("media_semantics"),
    }
    new_data["criterion"] = _criterion(contract, data.get("criterion"))
    if new_data != data:
        item.template_data = new_data
        changed += 1
    return changed


def run_seed() -> int:
    contracts = _load_contract()
    db = SessionLocal()
    changed = 0
    try:
        runtime_items = db.query(ContentItem).filter(ContentItem.kind == "pretest_question").all()
        by_canonical = {
            str((item.template_data or {}).get("canonical_id") or item.stable_key): item
            for item in runtime_items
        }
        for contract in contracts:
            canonical = str(contract["canonical_id"])
            item = by_canonical.get(canonical)
            if item is None:
                raise RuntimeError(f"Missing runtime pretest item: {canonical}")
            changed += _apply_item(item, contract)

        marked = sum(1 for item in runtime_items if (item.template_data or {}).get("pretest_experience_version") == VERSION)
        if marked != 30:
            raise RuntimeError(f"Expected {VERSION} on 30 pretest items, got {marked}")
        db.commit()
        return changed
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print(f"Pretest experience overlay OK: changed={run_seed()}")
