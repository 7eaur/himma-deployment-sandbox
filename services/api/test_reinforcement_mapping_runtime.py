"""Runtime tests for the reviewed skill-family reinforcement resolver."""

import seed

from reinforcement_mapping import mapping_for_skill, recommended_reinforcement_for_skill
from db.database import SessionLocal
from db.models import ContentItem, Skill, Student


def test_mapping_lookup_uses_skill_family_contract():
    shadda = mapping_for_skill(level_id=2, skill_code="shadda_word_reading")
    assert shadda is not None
    assert shadda["family"] == "shadda"
    assert shadda["candidates"] == ["L2-REIN-09"]


def test_sukoon_uses_approved_existing_supporting_reinforcement():
    sukoon = mapping_for_skill(level_id=2, skill_code="sukoon_word_reading")
    assert sukoon is not None
    assert sukoon["coverage"] == "supporting"
    assert sukoon["candidates"] == ["L2-REIN-02"]


def test_resolver_can_use_existing_original_reinforcement_without_exact_skill_id():
    seed.run_seed()
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        skill = db.query(Skill).filter(Skill.canonical_skill_id == "visual_letter_discrimination").one()
        selected_id = recommended_reinforcement_for_skill(
            db,
            student_id=student.id,
            level_id=1,
            weakest_skill_id=skill.id,
        )
        assert selected_id is not None
        item = db.query(ContentItem).filter(ContentItem.id == selected_id).one()
        assert item.level_id == 1
        assert item.kind == "reinforcement_activity"
        assert item.status == "approved"
        assert (item.template_data or {}).get("canonical_id") == "L1-REIN-01"
    finally:
        db.close()


def test_resolver_does_not_fake_unseeded_new_candidate():
    seed.run_seed()
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        skill = db.query(Skill).filter(Skill.canonical_skill_id == "shadda_word_reading").one()
        selected_id = recommended_reinforcement_for_skill(
            db,
            student_id=student.id,
            level_id=2,
            weakest_skill_id=skill.id,
        )
        # L2-REIN-09 belongs to the versioned extension and is deliberately not
        # treated as available until the reviewed extension seeding slice lands.
        assert selected_id is None
    finally:
        db.close()
