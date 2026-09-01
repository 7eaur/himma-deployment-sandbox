"""Normalize student-facing learning display data without changing academic scoring data."""
from __future__ import annotations

from copy import deepcopy

from db.database import SessionLocal
from db.models import ContentItem

LEARNING_DISPLAY_VERSION = "HIMMA-LEARNING-2026-09-01-R2"
LISTEN = {"listen_choose_one", "listen_choose_image", "listen_choose_many"}
NO_TEXT = {"read_aloud", "timed_read_aloud", "memory_sequence", "sequence", "build_word", "choose_image", "choose_many", "listen_choose_image", "listen_choose_many"}
LISTEN_WITH_VISIBLE_STIMULUS = {"L1-CORE-06"}


def canonical(item: ContentItem) -> str:
    return str((item.template_data or {}).get("canonical_id") or item.stable_key)


def _clean_stimulus(item: ContentItem, step) -> str:
    interaction = str((item.template_data or {}).get("canonical_interaction_type") or item.interaction_type)
    key = canonical(item)
    if interaction in NO_TEXT:
        return ""
    if interaction in LISTEN and key not in LISTEN_WITH_VISIBLE_STIMULUS:
        return ""

    text = str(step.prompt_text or "").strip()
    if not text:
        return ""
    text = text.replace("التعليمات:", "").strip()
    for marker in ("الخيارات:", "الصور:"):
        if marker in text:
            text = text.split(marker, 1)[0].strip()
    # The legacy catalog often stores `stimulus؛ option/option/option` in one field.
    # Only the segment before the Arabic semicolon is student stimulus.
    if "؛" in text:
        text = text.split("؛", 1)[0].strip()
    return text


def run_seed() -> dict[str, int]:
    db = SessionLocal()
    try:
        items = db.query(ContentItem).filter(ContentItem.kind.in_(["core_activity", "reinforcement_activity"])).all()
        if len(items) != 65:
            raise RuntimeError(f"Expected 65 learning items, got {len(items)}")
        changed = 0
        rounds = 0
        for item in items:
            data = deepcopy(item.template_data or {})
            experience = deepcopy(data.get("learning_experience") or {})
            projected_rounds = list(experience.get("rounds") or [])
            steps = sorted(item.steps, key=lambda step: step.order_index)
            if len(projected_rounds) != len(steps):
                raise RuntimeError(f"{canonical(item)} learning projection/step count mismatch")
            step_by_order = {int(step.order_index): step for step in steps}
            normalized = []
            for round_data in projected_rounds:
                row = dict(round_data)
                order = int(row.get("round_number") or 0)
                step = step_by_order.get(order)
                if step is None:
                    raise RuntimeError(f"{canonical(item)} missing round {order}")
                row["stimulus_text"] = _clean_stimulus(item, step)
                normalized.append(row)
                rounds += 1
            experience["version"] = LEARNING_DISPLAY_VERSION
            experience["rounds"] = normalized
            data["learning_experience_version"] = LEARNING_DISPLAY_VERSION
            data["learning_experience"] = experience
            if data != (item.template_data or {}):
                item.template_data = data
                changed += 1
        db.commit()
        return {"learning_items": 65, "learning_rounds": rounds, "changed": changed}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print(f"Learning display R2 OK: {run_seed()}")
