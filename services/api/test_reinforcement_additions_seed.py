"""Database contract tests for the versioned M03 reinforcement additions."""

import seed
import seed_reinforcement_additions
from db.database import SessionLocal
from db.models import ContentItem


def test_versioned_reinforcement_seed_adds_18_without_mutating_original_105():
    seed.run_seed()
    db = SessionLocal()
    try:
        assert db.query(ContentItem).count() == 105
        assert db.query(ContentItem).filter(ContentItem.kind == "reinforcement_activity").count() == 15
    finally:
        db.close()

    assert seed_reinforcement_additions.run_seed() == 18

    db = SessionLocal()
    try:
        assert db.query(ContentItem).count() == 123
        assert db.query(ContentItem).filter(ContentItem.kind == "reinforcement_activity").count() == 33
        distribution = {
            level: db.query(ContentItem).filter(
                ContentItem.kind == "reinforcement_activity",
                ContentItem.level_id == level,
            ).count()
            for level in (1, 2, 3)
        }
        assert distribution == {1: 12, 2: 11, 3: 10}
    finally:
        db.close()


def test_extension_seed_is_idempotent_when_run_twice_after_base_seed():
    seed.run_seed()
    assert seed_reinforcement_additions.run_seed() == 18
    assert seed_reinforcement_additions.run_seed() == 0


def test_new_shadda_activity_is_runtime_addressable_by_canonical_id():
    seed.run_seed()
    seed_reinforcement_additions.run_seed()
    db = SessionLocal()
    try:
        item = next(
            row
            for row in db.query(ContentItem).filter(
                ContentItem.kind == "reinforcement_activity",
                ContentItem.level_id == 2,
            ).all()
            if (row.template_data or {}).get("canonical_id") == "L2-REIN-09"
        )
        assert item.status == "approved"
        assert item.template_data["target_skill_family"] == "shadda"
        assert len(item.steps) == 5
    finally:
        db.close()
