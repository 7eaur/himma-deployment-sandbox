"""Exact choice-cardinality contract for all core/reinforcement rounds."""
from __future__ import annotations

import seed_all
from content_runtime import canonical_id, canonical_interaction
from db.database import SessionLocal
from db.models import ContentItem
from learning_experience import _required_selection_count

SINGLE = {"choose_one", "listen_choose_one", "choose_image", "listen_choose_image"}
MULTI = {"choose_many", "listen_choose_many"}
ORDER = {"sequence", "memory_sequence", "build_word"}


def test_every_learning_round_exposes_exact_selection_cardinality_from_database():
    result = seed_all.run_seed_all()
    assert result["learning_experience_items"] == 65
    db = SessionLocal()
    errors: list[str] = []
    try:
        items = db.query(ContentItem).filter(ContentItem.kind.in_(["core_activity", "reinforcement_activity"])).all()
        for item in items:
            interaction = canonical_interaction(item)
            for step in item.steps:
                count = _required_selection_count(interaction, step)
                correct = len([option for option in step.options if option.is_correct])
                if interaction in SINGLE and count != 1:
                    errors.append(f"{canonical_id(item)}/R{step.order_index}: single count={count}")
                if interaction in MULTI and count != correct:
                    errors.append(f"{canonical_id(item)}/R{step.order_index}: multi count={count} correct={correct}")
                if interaction in ORDER and count != len(step.options):
                    errors.append(f"{canonical_id(item)}/R{step.order_index}: order count={count} options={len(step.options)}")
                if interaction not in SINGLE | MULTI | ORDER and count != 0:
                    errors.append(f"{canonical_id(item)}/R{step.order_index}: non-choice count={count}")
        assert not errors, "\n".join(errors)
    finally:
        db.close()
