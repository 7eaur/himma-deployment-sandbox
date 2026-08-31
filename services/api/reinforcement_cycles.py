"""Lifecycle service for targeted reinforcement and core verification."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from db.activity_models import ActivityStepResponse
from db.adaptation_models import AdaptationDecision
from db.models import Attempt, AttemptResponse, ContentItem, Student
from db.reinforcement_models import ReinforcementCycle


ACTIVE_STATUSES = {
    "reinforcement_pending",
    "reinforcement_in_progress",
    "verification_pending",
}


def _source_attempt_id(decision: AdaptationDecision) -> int | None:
    explanation = decision.explanation or {}
    attempts = explanation.get("attempts_newest_to_oldest") or []
    if attempts and attempts[0].get("attempt_id"):
        return int(attempts[0]["attempt_id"])
    if explanation.get("source_attempt_id"):
        return int(explanation["source_attempt_id"])
    if decision.snapshot_key and decision.snapshot_key.startswith("immediate:"):
        try:
            return int(decision.snapshot_key.split(":", 1)[1])
        except (TypeError, ValueError):
            return None
    return None


def failed_step_ids(db: Session, source_attempt: Attempt) -> list[int]:
    """Return only the source steps that contain real incorrect evidence."""
    item = db.query(ContentItem).filter(ContentItem.id == source_attempt.item_id).first()
    if not item:
        return []

    failed: list[int] = []
    for step in item.steps:
        structured = (
            db.query(ActivityStepResponse)
            .filter(
                ActivityStepResponse.attempt_id == source_attempt.id,
                ActivityStepResponse.step_id == step.id,
            )
            .order_by(ActivityStepResponse.attempt_no.desc())
            .first()
        )
        if structured:
            payload = structured.response_payload or {}
            if payload.get("declared_media_gap_skip") or payload.get("temporary_audio_skip"):
                continue
            if structured.is_correct is False:
                failed.append(step.id)
            continue

        response = db.query(AttemptResponse).filter(
            AttemptResponse.attempt_id == source_attempt.id,
            AttemptResponse.step_id == step.id,
        ).first()
        if response is not None and response.is_correct is False:
            failed.append(step.id)
    return failed


def ensure_cycle(
    db: Session,
    *,
    student: Student,
    session_id: int,
    decision: AdaptationDecision,
    reinforcement_attempt_id: int | None,
) -> ReinforcementCycle | None:
    """Create one durable cycle for a mapped support decision."""
    if decision.action != "support" or decision.recommended_item_id is None:
        return None

    existing = db.query(ReinforcementCycle).filter(
        ReinforcementCycle.decision_id == decision.id
    ).first()
    if existing:
        if reinforcement_attempt_id and existing.reinforcement_attempt_id is None:
            existing.reinforcement_attempt_id = reinforcement_attempt_id
            existing.status = "reinforcement_in_progress"
            existing.updated_at = datetime.now(timezone.utc)
        return existing

    source_attempt_id = _source_attempt_id(decision)
    if source_attempt_id is None:
        return None
    source_attempt = db.query(Attempt).filter(
        Attempt.id == source_attempt_id,
        Attempt.session_id == session_id,
    ).first()
    if not source_attempt:
        return None
    failed = failed_step_ids(db, source_attempt)
    if not failed:
        # No concrete failed step means there is nothing safe to verify later.
        return None

    cycle = ReinforcementCycle(
        student_id=student.id,
        session_id=session_id,
        decision_id=decision.id,
        source_attempt_id=source_attempt.id,
        source_step_ids=failed,
        reinforcement_item_id=decision.recommended_item_id,
        reinforcement_attempt_id=reinforcement_attempt_id,
        status="reinforcement_in_progress" if reinforcement_attempt_id else "reinforcement_pending",
    )
    db.add(cycle)
    db.flush()
    return cycle


def mark_reinforcement_completed(
    db: Session,
    *,
    cycle: ReinforcementCycle,
) -> Attempt | None:
    """Move the cycle to verification and reopen only its source attempt."""
    if cycle.status in {"verified", "escalated"}:
        return None
    reinforcement_attempt = (
        db.query(Attempt).filter(Attempt.id == cycle.reinforcement_attempt_id).first()
        if cycle.reinforcement_attempt_id
        else None
    )
    if not reinforcement_attempt or reinforcement_attempt.status != "completed":
        return None

    source_attempt = db.query(Attempt).filter(Attempt.id == cycle.source_attempt_id).first()
    if not source_attempt:
        cycle.status = "escalated"
        cycle.escalation_reason = "source_attempt_missing"
        cycle.updated_at = datetime.now(timezone.utc)
        return None

    source_attempt.status = "in_progress"
    source_attempt.completed_at = None
    cycle.status = "verification_pending"
    cycle.updated_at = datetime.now(timezone.utc)
    return source_attempt


def active_verification_cycle(
    db: Session,
    *,
    source_attempt_id: int,
    step_id: int | None = None,
) -> ReinforcementCycle | None:
    query = db.query(ReinforcementCycle).filter(
        ReinforcementCycle.source_attempt_id == source_attempt_id,
        ReinforcementCycle.status == "verification_pending",
    )
    cycle = query.order_by(ReinforcementCycle.id.desc()).first()
    if cycle is None:
        return None
    if step_id is not None and step_id not in (cycle.source_step_ids or []):
        return None
    return cycle


def verification_response_count(db: Session, *, cycle: ReinforcementCycle, step_id: int) -> int:
    rows = db.query(ActivityStepResponse).filter(
        ActivityStepResponse.attempt_id == cycle.source_attempt_id,
        ActivityStepResponse.step_id == step_id,
    ).all()
    return sum(
        1
        for row in rows
        if (row.response_payload or {}).get("reinforcement_cycle_id") == cycle.id
        and (row.response_payload or {}).get("reinforcement_verification") is True
    )


def finish_verification_step(
    db: Session,
    *,
    cycle: ReinforcementCycle,
    step_id: int,
    is_correct: bool,
) -> str:
    """Update bounded verification state after one source-step verification."""
    if cycle.status != "verification_pending":
        return cycle.status

    if is_correct:
        verified_steps = set((cycle.source_step_ids or []))
        remaining = []
        for candidate in verified_steps:
            if candidate == step_id:
                continue
            count = verification_response_count(db, cycle=cycle, step_id=candidate)
            latest = (
                db.query(ActivityStepResponse)
                .filter(
                    ActivityStepResponse.attempt_id == cycle.source_attempt_id,
                    ActivityStepResponse.step_id == candidate,
                )
                .order_by(ActivityStepResponse.attempt_no.desc())
                .first()
            )
            if count == 0 or latest is None or latest.is_correct is not True:
                remaining.append(candidate)
        if not remaining:
            cycle.status = "verified"
            cycle.completed_at = datetime.now(timezone.utc)
        cycle.updated_at = datetime.now(timezone.utc)
        return cycle.status

    cycle.verification_round += 1
    if cycle.verification_round >= cycle.max_verification_rounds:
        cycle.status = "escalated"
        cycle.escalation_reason = "verification_failed_after_bounded_retries"
        cycle.completed_at = datetime.now(timezone.utc)
    cycle.updated_at = datetime.now(timezone.utc)
    return cycle.status
