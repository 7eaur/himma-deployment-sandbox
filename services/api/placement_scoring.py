"""Source-grounded pre/post assessment scoring and initial placement policy.

The approved Himma assessment has three sections:

* readiness: 10 items / 20 points;
* word building and reading: 12 items / 40 points;
* fluency and comprehension: 8 items / 40 points.

The source explicitly fixes the L1 readiness gate at 12/20.  It does not fix
numeric thresholds for the word-reading gate or text-accuracy gate required for
L3 placement.  This module therefore never invents those values: L3 is only
final when explicitly configured gates and their evidence are supplied.

Neutral/unresolved evidence is excluded from the section average and marks the
placement provisional.  It is never converted to an academic error.
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
READINESS_GATE_POINTS = Decimal("12")
TOTAL_L1_THRESHOLD = Decimal("50")
TOTAL_L3_THRESHOLD = Decimal("80")
SCORE_QUANT = Decimal("0.01")


@dataclass(frozen=True)
class AssessmentEvidence:
    """One assessment item's normalized academic evidence.

    ``score`` is in [0, 1]. ``None`` means academically neutral evidence such
    as an unresolved/invalid audio sample or an approved temporary media gap.
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
    """Explicit, approved L3 gate thresholds.

    ``None`` means the project has not yet approved/configured the numeric
    threshold.  No default is intentionally provided.
    """

    word_reading_min_accuracy: Optional[Decimal] = None
    text_accuracy_min: Optional[Decimal] = None


@dataclass(frozen=True)
class PlacementEvidence:
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
    """Calculate 20/40/40 section-normalised score without penalising neutral evidence."""

    grouped: dict[int, list[Optional[Decimal]]] = {1: [], 2: [], 3: []}
    for signal in evidence:
        if signal.section_id not in grouped:
            raise ValueError(f"Unsupported assessment section: {signal.section_id}")
        grouped[signal.section_id].append(
            None if signal.score is None else _normalise_score(signal.score)
        )

    sections: dict[int, SectionResult] = {}
    reasons: list[str] = []
    total = Decimal("0")

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
            points = (average * max_points).quantize(SCORE_QUANT, rounding=ROUND_HALF_UP)
        else:
            points = Decimal("0.00")
            reasons.append(f"section_{section_id}_has_no_valid_evidence")

        sections[section_id] = SectionResult(
            section_id=section_id,
            expected_items=expected,
            observed_items=len(values),
            valid_items=len(valid),
            neutral_items=neutral_count,
            points=points,
            max_points=max_points,
        )
        total += points

    total = total.quantize(SCORE_QUANT, rounding=ROUND_HALF_UP)
    return AssessmentScore(
        total_points=total,
        sections=sections,
        provisional=bool(reasons),
        provisional_reasons=tuple(reasons),
    )


def decide_initial_placement(
    score: AssessmentScore,
    *,
    gate_config: L3GateConfig = L3GateConfig(),
    gate_evidence: PlacementEvidence = PlacementEvidence(),
) -> PlacementDecision:
    """Apply approved placement rules without manufacturing missing L3 thresholds."""

    readiness = score.sections[1].points

    if score.total_points < TOTAL_L1_THRESHOLD or readiness < READINESS_GATE_POINTS:
        return PlacementDecision(
            assigned_level=1,
            status="provisional" if score.provisional else "final",
            reason=(
                "readiness_below_12_of_20"
                if readiness < READINESS_GATE_POINTS
                else "total_below_50"
            ),
        )

    if score.total_points < TOTAL_L3_THRESHOLD:
        return PlacementDecision(
            assigned_level=2,
            status="provisional" if score.provisional else "final",
            reason="total_between_50_and_79_99",
        )

    # The approved source requires word-reading and text-accuracy gates for L3,
    # but does not define their numeric thresholds.  Missing configuration is a
    # real project blocker, not permission to invent a value.
    if (
        gate_config.word_reading_min_accuracy is None
        or gate_config.text_accuracy_min is None
    ):
        return PlacementDecision(
            assigned_level=2,
            status="provisional",
            reason="l3_gate_thresholds_not_approved_or_configured",
        )

    if (
        gate_evidence.word_reading_accuracy is None
        or gate_evidence.text_accuracy is None
    ):
        return PlacementDecision(
            assigned_level=2,
            status="provisional",
            reason="l3_gate_evidence_missing_or_neutral",
        )

    if gate_evidence.word_reading_accuracy < gate_config.word_reading_min_accuracy:
        return PlacementDecision(
            assigned_level=2,
            status="provisional" if score.provisional else "final",
            reason="word_reading_gate_not_met",
        )

    if gate_evidence.text_accuracy < gate_config.text_accuracy_min:
        return PlacementDecision(
            assigned_level=2,
            status="provisional" if score.provisional else "final",
            reason="text_accuracy_gate_not_met",
        )

    return PlacementDecision(
        assigned_level=3,
        status="provisional" if score.provisional else "final",
        reason="total_and_approved_l3_gates_met",
    )
