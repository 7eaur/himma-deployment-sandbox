"""Regression tests for current-choice lifecycle and media-card invariants."""
from __future__ import annotations

from conftest import TestingSessionLocal
from content_runtime import step_assets
from db.models import ContentItem, ContentOption, ContentStep, Skill
from seed_active_option_contract import _reconcile_exact


def _item(db, *, canonical="TEST-OPTIONS", interaction="choose_one"):
    skill = Skill(
        skill_key=f"skill-{canonical}",
        canonical_skill_id=f"skill-{canonical}",
        name="اختبار الخيارات",
        description="test",
        level_id=1,
    )
    db.add(skill)
    db.flush()
    item = ContentItem(
        stable_key=canonical,
        kind="core_activity",
        level_id=1,
        skill_id=skill.id,
        interaction_type="multiple_choice",
        order_index=1,
        version="test",
        status="approved",
        checksum="a" * 64,
        template_data={
            "canonical_id": canonical,
            "canonical_interaction_type": interaction,
            "db_runtime": {
                "version": "HIMMA-DB-RUNTIME-1.0",
                "rounds": [],
            },
        },
    )
    db.add(item)
    db.flush()
    step = ContentStep(item_id=item.id, order_index=1, prompt_text="اختر")
    db.add(step)
    db.flush()
    return item, step


def test_retired_options_stay_in_history_but_leave_runtime_relationship():
    db = TestingSessionLocal()
    try:
        item, step = _item(db)
        current = ContentOption(step_id=step.id, text="ب", is_correct=True, order_index=1, is_active=True)
        stale = ContentOption(step_id=step.id, text="بـ", is_correct=False, order_index=2, is_active=True)
        duplicate = ContentOption(step_id=step.id, text="بـ", is_correct=False, order_index=3, is_active=True)
        db.add_all([current, stale, duplicate])
        db.commit()

        activated, retired = _reconcile_exact(db, step, ["ب", "بـ"])
        db.commit()
        assert activated == 0
        assert retired == 1

        stale_id = duplicate.id
        db.expire_all()
        loaded = db.query(ContentStep).filter(ContentStep.id == step.id).one()
        assert [option.text for option in loaded.options] == ["ب", "بـ"]
        historical = db.query(ContentOption).filter(ContentOption.id == stale_id).one()
        assert historical.is_active is False
    finally:
        db.close()


def test_step_assets_emit_one_image_card_per_active_option_and_keep_context_unmapped():
    db = TestingSessionLocal()
    try:
        item, step = _item(db, canonical="TEST-IMAGE", interaction="choose_image")
        first = ContentOption(step_id=step.id, text="الشمس", is_correct=True, order_index=1, is_active=True)
        second = ContentOption(step_id=step.id, text="القمر", is_correct=False, order_index=2, is_active=True)
        db.add_all([first, second])
        db.flush()
        data = dict(item.template_data or {})
        data["db_runtime"] = {
            "version": "HIMMA-DB-RUNTIME-1.0",
            "rounds": [{
                "order_index": 1,
                "source": {},
                "media_gaps": [],
                "assets": [
                    {"asset_id": "IMG-SUN", "asset_type": "image", "usage": "choice", "semantic_text": "الشمس", "option_order_index": 1},
                    {"asset_id": "IMG-SUN-DUP", "asset_type": "image", "usage": "choice", "semantic_text": "الشمس", "option_order_index": 1},
                    {"asset_id": "IMG-MOON", "asset_type": "image", "usage": "choice", "semantic_text": "القمر", "option_order_index": 2},
                    {"asset_id": "IMG-CONTEXT", "asset_type": "image", "usage": "illustration", "semantic_text": "صورة مساعدة", "option_order_index": 2},
                ],
            }],
        }
        item.template_data = data
        db.commit()
        db.expire_all()

        loaded_item = db.query(ContentItem).filter(ContentItem.id == item.id).one()
        loaded_step = loaded_item.steps[0]
        assets = step_assets(loaded_item, loaded_step)
        option_assets = [asset for asset in assets if asset["option_id"] is not None]
        assert [asset["option_id"] for asset in option_assets] == [first.id, second.id]
        assert len(option_assets) == 2
        context = next(asset for asset in assets if asset["asset_id"] == "IMG-CONTEXT")
        assert context["option_id"] is None
    finally:
        db.close()
