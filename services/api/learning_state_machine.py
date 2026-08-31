"""Pure policy primitives for the Himma learning journey.

This module contains no database mutations. It is the canonical policy
vocabulary separating one-activity outcome, mastery trend, level promotion and
L3 journey completion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ActivityOutcome = Literal["pass", "guided_retry", "reinforcement"]
JourneyOutcome = Literal["continue_level", "promote", "journey_complete"]

PASS_THRESHOLD = 80.0
GUIDED_RETRY_THRESHOLD = 70.0
LEVEL_MIN = 1
LEVEL_MAX = 3
CORE_ACTIVITIES_PER_LEVEL = 10
EARLY_PROMOTION_MIN_CORE = 6
EARLY_PROMOTION_MASTERY = 85.0
CRITICAL_SKILL_FLOOR = 70.0
POLICY_VERSION = "HIMMA_ADAPTIVE_V4_PILOT"


@dataclass(frozen=True)
class ActivityState:
    outcome: ActivityOutcome
    score: float
    reason: str


@dataclass(frozen=True)
class LevelState:
    outcome: JourneyOutcome
    current_level: int
    next_level: int | None
    reason: str


def classify_activity_score(score: float) -> ActivityState:
    """Classify one completed activity using the approved learning boundaries."""
    if score < 0 or score > 100:
        raise ValueError("activity score must be between 0 and 100")
    if score >= PASS_THRESHOLD:
        return ActivityState("pass", score, "activity_passed")
    if score >= GUIDED_RETRY_THRESHOLD:
        return ActivityState("guided_retry", score, "activity_needs_guided_retry")
    return ActivityState("reinforcement", score, "activity_below_70")


def level_completion_state(
    *,
    current_level: int,
    completed_core_count: int,
    mastery_score: float,
    unresolved_reinforcement: bool,
    critical_skill_coverage_ok: bool,
    minimum_critical_skill_score: float | None,
    supervisor_review_pending: bool,
) -> LevelState:
    """Return the pilot V4 journey state.

    L1/L2 may promote early only after at least six valid Core activities plus
    the 85 mastery and critical-skill gates. This is a versioned pilot policy,
    not a diagnostic standard. L3 remains a completion stage: all ten Core
    activities are required before the learning journey is considered complete.
    """
    if current_level < LEVEL_MIN or current_level > LEVEL_MAX:
        raise ValueError("current_level must be between 1 and 3")
    if completed_core_count < 0 or completed_core_count > CORE_ACTIVITIES_PER_LEVEL:
        raise ValueError("completed_core_count must be between 0 and 10")
    if mastery_score < 0 or mastery_score > 100:
        raise ValueError("mastery_score must be between 0 and 100")

    if unresolved_reinforcement:
        return LevelState("continue_level", current_level, current_level, "reinforcement_pending")
    if supervisor_review_pending:
        return LevelState("continue_level", current_level, current_level, "supervisor_review_pending")
    if not critical_skill_coverage_ok:
        return LevelState("continue_level", current_level, current_level, "critical_skill_coverage_pending")
    if minimum_critical_skill_score is None:
        return LevelState("continue_level", current_level, current_level, "critical_skill_policy_unverified")
    if minimum_critical_skill_score < CRITICAL_SKILL_FLOOR:
        return LevelState("continue_level", current_level, current_level, "critical_skill_below_floor")

    if current_level == LEVEL_MAX:
        if completed_core_count < CORE_ACTIVITIES_PER_LEVEL:
            return LevelState("continue_level", current_level, current_level, "level_three_evidence_incomplete")
        return LevelState("journey_complete", current_level, None, "level_three_complete")

    if completed_core_count < EARLY_PROMOTION_MIN_CORE:
        return LevelState("continue_level", current_level, current_level, "minimum_core_evidence_pending")
    if mastery_score < EARLY_PROMOTION_MASTERY:
        return LevelState("continue_level", current_level, current_level, "promotion_mastery_pending")

    return LevelState("promote", current_level, current_level + 1, "early_promotion_gates_passed")
