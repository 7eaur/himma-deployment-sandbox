from decimal import Decimal

from placement_scoring import (
    AssessmentEvidence,
    L3GateConfig,
    PlacementEvidence,
    decide_initial_placement,
    score_assessment,
)


def _section(section_id: int, count: int, score: str):
    return [AssessmentEvidence(section_id, Decimal(score)) for _ in range(count)]


def _score(readiness: str, word: str, fluency: str):
    return score_assessment(
        _section(1, 10, readiness)
        + _section(2, 12, word)
        + _section(3, 8, fluency)
    )


def test_section_weights_are_20_40_40():
    score = _score("1", "1", "1")
    assert score.sections[1].points == Decimal("20.00")
    assert score.sections[2].points == Decimal("40.00")
    assert score.sections[3].points == Decimal("40.00")
    assert score.total_points == Decimal("100.00")
    assert score.provisional is False


def test_readiness_below_12_of_20_forces_level_one_even_with_high_total():
    # 55% readiness = 11/20, while the other two sections are perfect.
    score = _score("0.55", "1", "1")
    assert score.total_points == Decimal("91.00")
    decision = decide_initial_placement(score)
    assert decision.assigned_level == 1
    assert decision.status == "final"
    assert decision.reason == "readiness_below_12_of_20"


def test_readiness_exactly_12_does_not_trigger_l1_gate():
    score = _score("0.60", "0.50", "0.50")
    assert score.sections[1].points == Decimal("12.00")
    assert score.total_points == Decimal("52.00")
    decision = decide_initial_placement(score)
    assert decision.assigned_level == 2
    assert decision.status == "final"


def test_total_below_50_is_level_one():
    score = _score("0.60", "0.45", "0.45")
    assert score.total_points == Decimal("48.00")
    decision = decide_initial_placement(score)
    assert decision.assigned_level == 1
    assert decision.reason == "total_below_50"


def test_total_50_to_below_80_is_level_two():
    score = _score("0.75", "0.70", "0.70")
    assert score.total_points == Decimal("71.00")
    decision = decide_initial_placement(score)
    assert decision.assigned_level == 2
    assert decision.status == "final"


def test_high_total_does_not_invent_missing_l3_thresholds():
    score = _score("1", "1", "1")
    decision = decide_initial_placement(score)
    assert decision.assigned_level == 2
    assert decision.status == "provisional"
    assert decision.reason == "l3_gate_thresholds_not_approved_or_configured"


def test_configured_l3_gates_can_make_final_level_three_decision():
    score = _score("1", "1", "1")
    decision = decide_initial_placement(
        score,
        gate_config=L3GateConfig(
            word_reading_min_accuracy=Decimal("0.80"),
            text_accuracy_min=Decimal("0.80"),
        ),
        gate_evidence=PlacementEvidence(
            word_reading_accuracy=Decimal("0.90"),
            text_accuracy=Decimal("0.85"),
        ),
    )
    assert decision.assigned_level == 3
    assert decision.status == "final"
    assert decision.reason == "total_and_approved_l3_gates_met"


def test_configured_l3_gate_failure_keeps_level_two():
    score = _score("1", "1", "1")
    decision = decide_initial_placement(
        score,
        gate_config=L3GateConfig(
            word_reading_min_accuracy=Decimal("0.80"),
            text_accuracy_min=Decimal("0.80"),
        ),
        gate_evidence=PlacementEvidence(
            word_reading_accuracy=Decimal("0.75"),
            text_accuracy=Decimal("0.95"),
        ),
    )
    assert decision.assigned_level == 2
    assert decision.status == "final"
    assert decision.reason == "word_reading_gate_not_met"


def test_neutral_evidence_is_excluded_not_scored_as_wrong_and_marks_provisional():
    evidence = (
        _section(1, 9, "1")
        + [AssessmentEvidence(1, None)]
        + _section(2, 12, "1")
        + _section(3, 8, "1")
    )
    score = score_assessment(evidence)
    assert score.sections[1].points == Decimal("20.00")
    assert score.sections[1].neutral_items == 1
    assert score.total_points == Decimal("100.00")
    assert score.provisional is True
    assert "section_1_neutral_evidence_1" in score.provisional_reasons


def test_missing_item_count_marks_score_provisional():
    score = score_assessment(
        _section(1, 9, "1")
        + _section(2, 12, "1")
        + _section(3, 8, "1")
    )
    assert score.provisional is True
    assert "section_1_item_count_9_expected_10" in score.provisional_reasons
