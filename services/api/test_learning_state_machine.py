import pytest

from learning_state_machine import classify_activity_score, level_completion_state


@pytest.mark.parametrize(
    ("score", "outcome"),
    [
        (100, "pass"),
        (80, "pass"),
        (79.9999, "guided_retry"),
        (70, "guided_retry"),
        (69.9999, "reinforcement"),
        (0, "reinforcement"),
    ],
)
def test_activity_state_boundaries(score, outcome):
    assert classify_activity_score(score).outcome == outcome


@pytest.mark.parametrize("score", [-0.01, 100.01])
def test_activity_state_rejects_invalid_score(score):
    with pytest.raises(ValueError):
        classify_activity_score(score)


def _state(**overrides):
    payload = {
        "current_level": 1,
        "completed_core_count": 6,
        "mastery_score": 90,
        "unresolved_reinforcement": False,
        "critical_skill_coverage_ok": True,
        "minimum_critical_skill_score": 80,
        "supervisor_review_pending": False,
    }
    payload.update(overrides)
    return level_completion_state(**payload)


def test_early_promotion_requires_at_least_six_core_activities():
    state = _state(completed_core_count=5)
    assert state.outcome == "continue_level"
    assert state.reason == "minimum_core_evidence_pending"

    promoted = _state(completed_core_count=6)
    assert (promoted.outcome, promoted.next_level) == ("promote", 2)


def test_early_promotion_requires_85_mastery():
    below = _state(mastery_score=84.9999)
    assert below.outcome == "continue_level"
    assert below.reason == "promotion_mastery_pending"
    assert _state(mastery_score=85).outcome == "promote"


def test_promotion_waits_for_reinforcement_review_and_critical_skill_gates():
    reinforcement = _state(unresolved_reinforcement=True)
    assert reinforcement.reason == "reinforcement_pending"

    review = _state(supervisor_review_pending=True)
    assert review.reason == "supervisor_review_pending"

    coverage = _state(critical_skill_coverage_ok=False)
    assert coverage.reason == "critical_skill_coverage_pending"

    unverified = _state(minimum_critical_skill_score=None)
    assert unverified.reason == "critical_skill_policy_unverified"

    low_critical = _state(minimum_critical_skill_score=69.9999)
    assert low_critical.reason == "critical_skill_below_floor"


def test_level_one_and_two_promote_only_one_level():
    first = _state(current_level=1)
    second = _state(current_level=2)
    assert (first.outcome, first.next_level) == ("promote", 2)
    assert (second.outcome, second.next_level) == ("promote", 3)


def test_level_three_still_requires_all_ten_core_before_journey_completion():
    early = _state(current_level=3, completed_core_count=6)
    assert early.outcome == "continue_level"
    assert early.reason == "level_three_evidence_incomplete"

    completed = _state(current_level=3, completed_core_count=10)
    assert completed.outcome == "journey_complete"
    assert completed.next_level is None


@pytest.mark.parametrize("score", [-0.01, 100.01])
def test_level_state_rejects_invalid_mastery(score):
    with pytest.raises(ValueError):
        _state(mastery_score=score)
