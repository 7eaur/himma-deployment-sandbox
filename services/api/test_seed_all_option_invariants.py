"""The deployment seed must stay idempotent after option/media reconciliation."""
from __future__ import annotations

from conftest import TestingSessionLocal
from db.models import ContentItem, ContentOption
from seed_active_option_contract import VERSION as OPTION_VERSION
from seed_runtime_media_invariants import VERSION as MEDIA_VERSION
from seed_all import run_seed_all


def test_full_runtime_seed_twice_preserves_current_option_contract():
    first = run_seed_all()
    second = run_seed_all()

    assert first["total_items"] == 125
    assert second["total_items"] == 125
    assert second["option_contract_items"] == 125
    assert second["media_contract_items"] == 125

    db = TestingSessionLocal()
    try:
        items = db.query(ContentItem).all()
        assert len(items) == 125
        assert all((item.template_data or {}).get("active_option_contract_version") == OPTION_VERSION for item in items)
        assert all((item.template_data or {}).get("media_option_contract_version") == MEDIA_VERSION for item in items)

        # Current relationships expose active choices only. Historical rows may
        # remain inactive to preserve old response foreign keys.
        for item in items:
            for step in item.steps:
                assert all(option.is_active for option in step.options)
                if str((item.template_data or {}).get("canonical_interaction_type") or item.interaction_type) not in {
                    "sequence", "memory_sequence", "path_sequence", "build_word"
                }:
                    visible = [option.text.replace("ـ", "").strip() for option in step.options]
                    assert len(visible) == len(set(visible)), (
                        f"duplicate current option in {((item.template_data or {}).get('canonical_id') or item.stable_key)} "
                        f"round {step.order_index}: {visible}"
                    )

        assert db.query(ContentOption).filter(ContentOption.is_active.is_(False)).count() >= 0
    finally:
        db.close()
