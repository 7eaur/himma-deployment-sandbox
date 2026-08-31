"""Recovery regressions for adaptation history scope and reward idempotency."""

from decimal import Decimal

import seed
from adaptation import (
    _add_reward_once,
    _previous_automatic_decision_same_level,
    decide_transition,
)
from conftest import TestingSessionLocal
from db.adaptation_models import AdaptationDecision, RewardEvent
from db.models import Student


def test_previous_low_is_scoped_to_the_same_level_and_never_demotes():
    """Low history is level-scoped, but repeated weakness never auto-demotes."""
    seed.run_seed()
    db = TestingSessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        student.current_level = 2

        db.add(AdaptationDecision(
            student_id=student.id,
            decision_source="automatic",
            action="support",
            mastery_score=Decimal("40"),
            previous_level=1,
            new_level=1,
            valid_attempt_count=3,
            consecutive_low_count=1,
            snapshot_key="regression:l1:first-low",
            explanation={"reason": "low_mastery_same_level_support"},
        ))
        db.commit()

        assert _previous_automatic_decision_same_level(db, student.id, 2) is None
        assert decide_transition(
            current_level=2,
            mastery=40,
            skill_coverage_ok=True,
            minimum_required_skill_score=40,
            previous_low=False,
        )[0:2] == ("support", 2)

        l2_first_low = AdaptationDecision(
            student_id=student.id,
            decision_source="automatic",
            action="support",
            mastery_score=Decimal("40"),
            previous_level=2,
            new_level=2,
            valid_attempt_count=3,
            consecutive_low_count=1,
            snapshot_key="regression:l2:first-low",
            explanation={"reason": "low_mastery_same_level_support"},
        )
        db.add(l2_first_low)
        db.commit()

        previous = _previous_automatic_decision_same_level(db, student.id, 2)
        assert previous is not None
        assert previous.id == l2_first_low.id
        assert decide_transition(
            current_level=2,
            mastery=40,
            skill_coverage_ok=True,
            minimum_required_skill_score=40,
            previous_low=True,
        )[0:2] == ("support", 2)
    finally:
        db.close()


def test_high_mastery_uses_six_core_pilot_gate_not_legacy_ten_core_gate():
    action, level, reason = decide_transition(
        current_level=1,
        mastery=95,
        skill_coverage_ok=True,
        minimum_required_skill_score=95,
        completed_core_count=5,
    )
    assert (action, level) == ("stay", 1)
    assert reason == "minimum_core_evidence_pending"

    action, level, reason = decide_transition(
        current_level=1,
        mastery=95,
        skill_coverage_ok=True,
        minimum_required_skill_score=95,
        completed_core_count=6,
    )
    assert (action, level) == ("promote", 2)
    assert reason == "early_promotion_gates_passed"


def test_reward_duplicate_uses_savepoint_and_keeps_outer_transaction_usable():
    """Duplicate reward races must not abort the caller's outer transaction."""
    seed.run_seed()
    db = TestingSessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        key = "regression:reward-concurrency"

        first = _add_reward_once(
            db,
            RewardEvent(
                student_id=student.id,
                attempt_id=None,
                reward_type="badge",
                reward_key=key,
                stars=None,
                label="اختبار التزامن",
                details={"source": "regression"},
            ),
        )
        duplicate = _add_reward_once(
            db,
            RewardEvent(
                student_id=student.id,
                attempt_id=None,
                reward_type="badge",
                reward_key=key,
                stars=None,
                label="اختبار التزامن",
                details={"source": "duplicate"},
            ),
        )

        assert first is True
        assert duplicate is False

        second_key = "regression:reward-after-conflict"
        assert _add_reward_once(
            db,
            RewardEvent(
                student_id=student.id,
                attempt_id=None,
                reward_type="badge",
                reward_key=second_key,
                stars=None,
                label="بعد التعارض",
                details={"source": "regression"},
            ),
        ) is True
        db.commit()

        assert db.query(RewardEvent).filter(
            RewardEvent.student_id == student.id,
            RewardEvent.reward_key == key,
        ).count() == 1
        assert db.query(RewardEvent).filter(
            RewardEvent.student_id == student.id,
            RewardEvent.reward_key == second_key,
        ).count() == 1
    finally:
        db.close()
