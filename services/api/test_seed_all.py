"""Full approved runtime content seed entrypoint contract."""

import seed_all
from db.database import SessionLocal
from db.models import ContentItem


def test_full_seed_creates_125_items_and_is_repeatable():
    first = seed_all.run_seed_all()
    second = seed_all.run_seed_all()

    assert first["baseline_items"] == 105
    assert first["reinforcement_items"] == 35
    assert first["total_items"] == 125
    assert first["v1_additions_created"] == 18
    assert first["v2_additions_created"] == 2
    assert first["additions_created"] == 20

    assert second["baseline_items"] == 105
    assert second["reinforcement_items"] == 35
    assert second["total_items"] == 125
    assert second["v1_additions_created"] == 0
    assert second["v2_additions_created"] == 0
    assert second["additions_created"] == 0

    db = SessionLocal()
    try:
        assert db.query(ContentItem).count() == 125
        assert db.query(ContentItem).filter(ContentItem.version == "HIMMA-CONTENT-1.0").count() == 105
        assert db.query(ContentItem).filter(ContentItem.version == "HIMMA-REINFORCEMENT-ADD-1.0").count() == 18
        assert db.query(ContentItem).filter(ContentItem.version == "HIMMA-REINFORCEMENT-ADD-2.0").count() == 2
    finally:
        db.close()
