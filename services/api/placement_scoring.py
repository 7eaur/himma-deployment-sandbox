"""Source-grounded pre/post assessment scoring and initial placement policy.

The approved Himma assessment has three sections:

* readiness: 10 items / 20 points;
* word building and reading: 12 items / 40 points;
* fluency and comprehension: 8 items / 40 points.

The latest accepted continuity decision (2026-09-05) resolves initial placement
by the final pretest score only:

* < 50 -> L1;
* 50 .. < 80 -> L2;
* 80 .. 100 -> L3.

Older experiments added a 12/20 readiness override and extra numeric L3 gates.
Those gates are retained only as compatibility data classes for historical
callers; they are not part of the active placement decision. Continuous
learning adaptation is a separate V4 policy and must not be mixed into initial
placement.

Neutral/unresolved evidence is excluded from the section average and marks the
score provisional. It is never converted to an academic error.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Mapping, Optional, Sequence


SECTION_COUNTS: Mapping[int, int] = {1: 10, 2: 12, 3: 8}
SECTION_MAX_POINTS: Mapping[int, Decimal] = {
    1: Decimal("20"),
    2: Decimal("40"),
    3: Decimal("40"),
}
TOTAL_L1_THRESHOLD = Decimal("50")
TOTAL_L3_THRESHOLD = Decimal("80")
SCORE_QUANT = Decimal("0.01")


@dataclass(frozen=True)
class AssessmentEvidence:
    """One assessment item's normalized academic evidence.

    ``score`` is in [0, 1]. ``None`` means academically neutral evidence such
    as an unresolved/invalid audio sample or an explicitly preserved historical
    neutral marker.
    """

    section_id: int
    score: Optional[Decimal]


@dataclass(frozen=True)
class SectionResult:
    section_id: int
    expected_items: int
    observed_items: int
    valid_items: int
    neutral_items: int
    points: Decimal
    max_points: Decimal


@dataclass(frozen=True)
class AssessmentScore:
    total_points: Decimal
    sections: Mapping[int, SectionResult]
    provisional: bool
    provisional_reasons: tuple[str, ...]


@dataclass(frozen=True)
class L3GateConfig:
    """Deprecated compatibility shape from the superseded L3-gate experiment."""

    word_reading_min_accuracy: Optional[Decimal] = None
    text_accuracy_min: Optional[Decimal] = None


@dataclass(frozen=True)
class PlacementEvidence:
    """Deprecated compatibility shape from the superseded L3-gate experiment."""

    word_reading_accuracy: Optional[Decimal] = None
    text_accuracy: Optional[Decimal] = None


@dataclass(frozen=True)
class PlacementDecision:
    assigned_level: int
    status: str  # "final" | "provisional"
    reason: str


def _normalise_score(value: Decimal) -> Decimal:
    decimal_value = Decimal(str(value))
    if decimal_value < 0 or decimal_value > 1:
        raise ValueError("Assessment item score must be within [0, 1]")
    return decimal_value


def score_assessment(evidence: Sequence[AssessmentEvidence]) -> AssessmentScore:
    """Calculate 20/40/40 section-normalised score without penalising neutral evidence.

    Section points are rounded to two decimals for presentation, but placement
    must use the mathematically combined score rounded only once at the end.
    Summing already-rounded section points can incorrectly turn 49.99 into
    50.00 or 79.99 into 80.00 and therefore move a student across a placement
    boundary.
    """

    grouped: dict[int, list[Optional[Decimal]]] = {1: [], 2: [], 3: []}
    for signal in evidence:
        if signal.section_id not in grouped:
            raise ValueError(f"Unsupported assessment section: {signal.section_id}")
        grouped[signal.section_id].append(
            None if signal.score is None else _normalise_score(signal.score)
        )

    sections: dict[int, SectionResult] = {}
    reasons: list[str] = []
    raw_total = Decimal("0")

    for section_id in (1, 2, 3):
        values = grouped[section_id]
        expected = SECTION_COUNTS[section_id]
        max_points = SECTION_MAX_POINTS[section_id]
        valid = [value for value in values if value is not None]
        neutral_count = sum(value is None for value in values)

        if len(values) != expected:
            reasons.append(
                f"section_{section_id}_item_count_{len(values)}_expected_{expected}"
            )

        if neutral_count:
            reasons.append(f"section_{section_id}_neutral_evidence_{neutral_count}")

        if valid:
            average = sum(valid, Decimal("0")) / Decimal(len(valid))
            raw_points = average * max_points
        else:
            raw_points = Decimal("0")
            reasons.append(f"section_{section_id}_has_no_valid_evidence")

        points = raw_points.quantize(SCORE_QUANT, rounding=ROUND_HALF_UP)
        sections[section_id] = SectionResult(
            section_id=section_id,
            expected_items=expected,
            observed_items=len(values),
            valid_items=len(valid),
            neutral_items=neutral_count,
            points=points,
            max_points=max_points,
        )
        raw_total += raw_points

    total = raw_total.quantize(SCORE_QUANT, rounding=ROUND_HALF_UP)
    return AssessmentScore(
        total_points=total,
        sections=sections,
        provisional=bool(reasons),
        provisional_reasons=tuple(reasons),
    )


def decide_initial_placement(
    score: AssessmentScore,
    *,
    gate_config: L3GateConfig | None = None,
    gate_evidence: PlacementEvidence | None = None,
) -> PlacementDecision:
    """Apply the 2026-09-05 accepted 50/80 starting-level boundaries.

    ``gate_config`` and ``gate_evidence`` are accepted only so historical code
    importing the old signature does not break. They deliberately do not change
    the active decision.
    """

    _ = (gate_config, gate_evidence)
    status = "provisional" if score.provisional else "final"

    if score.total_points < TOTAL_L1_THRESHOLD:
        return PlacementDecision(
            assigned_level=1,
            status=status,
            reason="total_below_50",
        )

    if score.total_points < TOTAL_L3_THRESHOLD:
        return PlacementDecision(
            assigned_level=2,
            status=status,
            reason="total_between_50_and_79_99",
        )

    return PlacementDecision(
        assigned_level=3,
        status=status,
        reason="total_at_or_above_80",
    )
