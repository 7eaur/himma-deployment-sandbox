"""Cross-boundary scenario matrix for the active Himma student policy.

The suite checks invariants across the policy state-space so future changes
cannot silently reintroduce demotion, multi-level jumps, stale-session evidence,
or superseded placement gates.
"""

from datetime import datetime, timezone

import pytest

import seed
from adaptation import _completed_core_count, _valid_signals, decide_transition
from conftest import TestingSessionLocal
from db.activity_models import ActivityStepResponse
from db.models import AssessmentSession, Attempt, ContentItem, ContentStep, Skill, Student
from learning_state_machine import classify_activity_score, level_completion_state


@pytest.mark.parametrize(
    ("score", "outcome"),
    [
        (0, "reinforcement"),
        (49.9999, "reinforcement"),
        (69.9999, "reinforcement"),
        (70, "guided_retry"),
        (79.9999, "guided_retry"),
        (80, "pass"),
        (100, "pass"),
    ],
)
def test_activity_outcome_full_boundary_set(score, outcome):
    assert classify_activity_score(score).outcome == outcome


@pytest.mark.parametrize("level", [1, 2])
@pytest.mark.parametrize("mastery", [0, 49.9999, 50, 69.9999, 70, 84.9999, 85, 100])
@pytest.mark.parametrize("completed_core", [0, 5, 6, 10])
@pytest.mark.parametrize("coverage", [False, True])
@pytest.mark.parametrize("critical_floor", [None, 69.9999, 70, 100])
def test_l1_l2_transition_matrix_never_demotes_or_skips_level(
    level,
    mastery,
    completed_core,
    coverage,
    critical_floor,
):
    action, new_level, _ = decide_transition(
        current_level=level,
        mastery=mastery,
        skill_coverage_ok=coverage,
        minimum_required_skill_score=critical_floor,
        completed_core_count=completed_core,
        critical_policy_configured=True,
    )

    assert new_level >= level
    assert new_level <= min(3, level + 1)
    assert action != "demote"

    if mastery < 50:
        assert (action, new_level) == ("support", level)
        return

    promotion_ready = (
        mastery >= 85
        and completed_core >= 6
        and coverage
        and critical_floor is not None
        and critical_floor >= 70
    )
    if promotion_ready:
        assert (action, new_level) == ("promote", level + 1)
    else:
        assert (action, new_level) == ("stay", level)


@pytest.mark.parametrize(
    ("reinforcement_pending", "review_pending", "expected_reason"),
    [
        (True, False, "promotion_blocked_by_reinforcement_cycle"),
        (False, True, "promotion_blocked_by_supervisor_review"),
    ],
)
def test_promotion_blockers_win_even_with_perfect_evidence(
    reinforcement_pending,
    review_pending,
    expected_reason,
):
    action, level, reason = decide_transition(
        current_level=2,
        mastery=100,
        skill_coverage_ok=True,
        minimum_required_skill_score=100,
        completed_core_count=10,
        unresolved_reinforcement=reinforcement_pending,
        supervisor_review_pending=review_pending,
    )
    assert (action, level, reason) == ("stay", 2, expected_reason)


@pytest.mark.parametrize("completed_core", range(0, 10))
def test_l3_never_completes_before_all_ten_core(completed_core):
    state = level_completion_state(
        current_level=3,
        completed_core_count=completed_core,
        mastery_score=100,
        unresolved_reinforcement=False,
        critical_skill_coverage_ok=True,
        minimum_critical_skill_score=100,
        supervisor_review_pending=False,
    )
    assert state.outcome == "continue_level"
    assert state.next_level == 3


def test_l3_full_evidence_completes_without_fictitious_level_four():
    state = level_completion_state(
        current_level=3,
        completed_core_count=10,
        mastery_score=100,
        unresolved_reinforcement=False,
        critical_skill_coverage_ok=True,
        minimum_critical_skill_score=100,
        supervisor_review_pending=False,
    )
    assert state.outcome == "journey_complete"
    assert state.next_level is None


def _create_scored_item(db, *, key: str, skill_id: int, order_index: int):
    item = ContentItem(
        stable_key=key,
        kind="core_activity",
        level_id=1,
        skill_id=skill_id,
        interaction_type="choose_one",
        order_index=order_index,
        version="scenario-matrix",
        status="approved",
        checksum=(key * 64)[:64],
        template_data={"canonical_id": key, "canonical_interaction_type": "choose_one"},
    )
    db.add(item)
    db.flush()
    step = ContentStep(item_id=item.id, order_index=1, prompt_text="اختبار نطاق الجلسة")
    db.add(step)
    db.flush()
    return item, step


def _complete_scored_attempt(db, *, session_id: int, item, step, is_correct: bool):
    attempt = Attempt(
        session_id=session_id,
        item_id=item.id,
        status="completed",
        completed_at=datetime.now(timezone.utc),
    )
    db.add(attempt)
    db.flush()
    db.add(ActivityStepResponse(
        attempt_id=attempt.id,
        step_id=step.id,
        attempt_no=1,
        response_payload={"selected_option_ids": [1]},
        is_correct=is_correct,
        hint_used=False,
        elapsed_seconds=1,
    ))
    db.flush()
    return attempt


def test_historical_level_session_evidence_isolated_from_fresh_session():
    seed.run_seed()
    db = TestingSessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        student.current_level = 1
        skill = Skill(
            skill_key="scenario-session-scope",
            name="اختبار عزل الجلسة",
            level_id=1,
            canonical_skill_id="scenario_session_scope",
        )
        db.add(skill)
        db.flush()

        old_session = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="completed",
            assigned_level=1,
            completed_at=datetime.now(timezone.utc),
        )
        fresh_session = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="in_progress",
            assigned_level=1,
        )
        db.add_all([old_session, fresh_session])
        db.flush()

        old_attempt_ids = []
        for index in range(1, 4):
            item, step = _create_scored_item(
                db,
                key=f"SCENARIO-OLD-{index}",
                skill_id=skill.id,
                order_index=500 + index,
            )
            old_attempt_ids.append(
                _complete_scored_attempt(
                    db,
                    session_id=old_session.id,
                    item=item,
                    step=step,
                    is_correct=True,
                ).id
            )

        fresh_item, fresh_step = _create_scored_item(
            db,
            key="SCENARIO-FRESH-1",
            skill_id=skill.id,
            order_index=600,
        )
        fresh_attempt = _complete_scored_attempt(
            db,
            session_id=fresh_session.id,
            item=fresh_item,
            step=fresh_step,
            is_correct=False,
        )
        db.commit()

        all_history = _valid_signals(db, student.id, 1)
        fresh_only = _valid_signals(db, student.id, 1, session_id=fresh_session.id)
        assert {signal.attempt_id for signal in all_history}.issuperset(old_attempt_ids)
        assert [signal.attempt_id for signal in fresh_only] == [fresh_attempt.id]
        assert _completed_core_count(db, student.id, 1, session_id=fresh_session.id) == 1
        assert _completed_core_count(db, student.id, 1) >= 4
    finally:
        db.close()
