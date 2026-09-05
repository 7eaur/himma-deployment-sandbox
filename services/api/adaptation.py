"""Adaptive learning policy for the Himma student journey.

V4 pilot invariants:
- newest three valid evidences are weighted 50/30/20;
- one activity: >=80 pass, 70..<80 guided retry, <70 targeted reinforcement;
- automatic demotion is forbidden;
- L1/L2 early promotion requires >=6 completed Core activities, weighted mastery
  >=85, explicit critical-skill coverage/floor, no unresolved reinforcement and
  no pending supervisor review;
- L3 is a completion level and still requires all ten Core activities;
- invalid/incomplete/media-gap/unresolved-audio evidence is neutral/excluded;
- current progression uses only evidence from the active learning session;
- reinforcement never falls back to random or cross-level content.

Initial pretest placement is a separate 50/80 policy and must never be mixed
with these continuous-learning gates.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.adaptation_models import AdaptationDecision, RewardEvent
from db.activity_models import ActivityStepResponse
from db.models import (
    AssessmentSession,
    Attempt,
    AttemptResponse,
    AudioSubmission,
    ContentItem,
    ContentStep,
    Skill,
    Student,
    User,
)
from db.reinforcement_models import ReinforcementCycle
from dependencies import get_current_student, get_current_user, get_db
from reinforcement_mapping import recommended_reinforcement_for_skill

router = APIRouter(tags=["Adaptation"])
ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "packages" / "content" / "src" / "adaptive_policy_v4_pilot.json"

WEIGHTS = (0.50, 0.30, 0.20)
PROMOTION_THRESHOLD = 85.0
SUPPORT_THRESHOLD = 50.0
REINFORCEMENT_THRESHOLD = 70.0
CRITICAL_SKILL_FLOOR = 70.0
EARLY_PROMOTION_MIN_CORE = 6
CORE_ACTIVITY_COUNT = 10
POLICY_VERSION = "HIMMA_ADAPTIVE_V4_PILOT"

BADGE_BY_LEVEL = {
    1: "مستكشف الحروف",
    2: "بطل الكلمات",
    3: "قارئ متميز",
}


@dataclass(frozen=True)
class AttemptSignal:
    attempt_id: int
    skill_id: int
    score: float


@dataclass(frozen=True)
class PromotionGateState:
    configured: bool
    coverage_ok: bool
    minimum_score: Optional[float]
    weakest_skill_id: Optional[int]
    critical_skill_ids: tuple[int, ...]
    critical_skill_codes: tuple[str, ...]


class ManualOverrideRequest(BaseModel):
    new_level: int = Field(ge=1, le=3)
    reason: str = Field(min_length=5, max_length=1000)


def _load_policy() -> dict:
    if not POLICY_PATH.exists():
        return {}
    try:
        payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if payload.get("policy_version") != POLICY_VERSION:
        return {}
    return payload


def weighted_mastery(newest_first_scores: list[float]) -> float:
    if len(newest_first_scores) != 3:
        raise ValueError("Exactly three valid scores are required")
    return round(sum(score * weight for score, weight in zip(newest_first_scores, WEIGHTS)), 4)


def decide_transition(
    *,
    current_level: int,
    mastery: float,
    skill_coverage_ok: bool,
    minimum_required_skill_score: Optional[float],
    previous_low: bool = False,
    level_complete: Optional[bool] = None,
    completed_core_count: Optional[int] = None,
    unresolved_reinforcement: bool = False,
    supervisor_review_pending: bool = False,
    critical_policy_configured: bool = True,
) -> tuple[str, int, str]:
    """Return the V4 continuous decision without automatic demotion.

    ``previous_low`` and ``level_complete`` remain accepted for compatibility
    with historical callers/tests. Runtime callers pass ``completed_core_count``
    explicitly. Historical low evidence can increase an audit counter but never
    lowers the assigned level.
    """
    if current_level < 1 or current_level > 3:
        raise ValueError("current_level must be between 1 and 3")
    if mastery < 0 or mastery > 100:
        raise ValueError("mastery must be between 0 and 100")

    if mastery < SUPPORT_THRESHOLD:
        return "support", current_level, "low_mastery_same_level_support"

    if unresolved_reinforcement:
        return "stay", current_level, "promotion_blocked_by_reinforcement_cycle"
    if supervisor_review_pending:
        return "stay", current_level, "promotion_blocked_by_supervisor_review"
    if not critical_policy_configured:
        return "stay", current_level, "critical_skill_policy_unverified"
    if not skill_coverage_ok:
        return "stay", current_level, "promotion_waiting_for_critical_skill_coverage"
    if minimum_required_skill_score is None:
        return "stay", current_level, "critical_skill_policy_unverified"
    if minimum_required_skill_score < CRITICAL_SKILL_FLOOR:
        return "stay", current_level, "promotion_blocked_by_critical_skill_floor"

    if current_level >= 3:
        if completed_core_count is not None and completed_core_count < CORE_ACTIVITY_COUNT:
            return "stay", current_level, "level_three_evidence_incomplete"
        return "stay", current_level, "top_level_mastery"

    if mastery < PROMOTION_THRESHOLD:
        return "stay", current_level, "promotion_mastery_pending"

    if completed_core_count is None:
        completed_core_count = CORE_ACTIVITY_COUNT if level_complete is True else 0
    if completed_core_count < EARLY_PROMOTION_MIN_CORE:
        return "stay", current_level, "minimum_core_evidence_pending"

    return "promote", current_level + 1, "early_promotion_gates_passed"


def _attempt_signal(db: Session, attempt: Attempt, item: ContentItem) -> Optional[AttemptSignal]:
    if attempt.status != "completed":
        return None

    scores: list[bool] = []
    for step in db.query(ContentStep).filter(ContentStep.item_id == item.id).order_by(ContentStep.order_index).all():
        structured = (
            db.query(ActivityStepResponse)
            .filter(
                ActivityStepResponse.attempt_id == attempt.id,
                ActivityStepResponse.step_id == step.id,
            )
            .order_by(ActivityStepResponse.attempt_no.desc())
            .first()
        )
        if structured:
            payload = structured.response_payload or {}
            if payload.get("declared_media_gap_skip") or payload.get("temporary_audio_skip"):
                continue
            scores.append(bool(structured.is_correct))
            continue

        response = db.query(AttemptResponse).filter(
            AttemptResponse.attempt_id == attempt.id,
            AttemptResponse.step_id == step.id,
        ).first()
        if not response:
            return None
        audio = db.query(AudioSubmission).filter(AudioSubmission.response_id == response.id).first()
        if audio and audio.status in {"pending", "rerecord_required", "uploaded"}:
            return None
        if response.is_correct is None:
            continue
        scores.append(bool(response.is_correct))

    if not scores:
        return None
    return AttemptSignal(
        attempt_id=attempt.id,
        skill_id=item.skill_id,
        score=round((sum(1 for value in scores if value) / len(scores)) * 100.0, 4),
    )


def _valid_signals(
    db: Session,
    student_id: int,
    level_id: int,
    session_id: int | None = None,
) -> list[AttemptSignal]:
    query = (
        db.query(Attempt, ContentItem)
        .join(AssessmentSession, AssessmentSession.id == Attempt.session_id)
        .join(ContentItem, ContentItem.id == Attempt.item_id)
        .filter(
            AssessmentSession.student_id == student_id,
            AssessmentSession.assigned_level == level_id,
            Attempt.status == "completed",
            ContentItem.level_id == level_id,
            ContentItem.kind.in_(["core_activity", "reinforcement_activity"]),
        )
    )
    if session_id is not None:
        query = query.filter(AssessmentSession.id == session_id)
    rows = query.order_by(Attempt.completed_at, Attempt.id).all()

    signals: list[AttemptSignal] = []
    for attempt, item in rows:
        signal = _attempt_signal(db, attempt, item)
        if signal is not None:
            signals.append(signal)
    return signals


def _completed_core_count(
    db: Session,
    student_id: int,
    level_id: int,
    session_id: int | None = None,
) -> int:
    query = (
        db.query(ContentItem.id)
        .join(Attempt, Attempt.item_id == ContentItem.id)
        .join(AssessmentSession, AssessmentSession.id == Attempt.session_id)
        .filter(
            AssessmentSession.student_id == student_id,
            AssessmentSession.assigned_level == level_id,
            Attempt.status == "completed",
            ContentItem.kind == "core_activity",
            ContentItem.level_id == level_id,
        )
    )
    if session_id is not None:
        query = query.filter(AssessmentSession.id == session_id)
    return query.distinct().count()


def _core_flow_complete(db: Session, student_id: int, level_id: int) -> bool:
    return _completed_core_count(db, student_id, level_id) >= CORE_ACTIVITY_COUNT


def _critical_skill_gate_state(
    db: Session,
    level_id: int,
    signals: list[AttemptSignal],
) -> PromotionGateState:
    policy = _load_policy()
    configured_codes = tuple(
        str(code)
        for code in (policy.get("critical_skill_codes_by_level", {}).get(str(level_id), []) or [])
        if str(code).strip()
    )
    if not configured_codes:
        return PromotionGateState(False, False, None, None, (), ())

    skills = db.query(Skill).filter(
        Skill.level_id == level_id,
        Skill.canonical_skill_id.in_(configured_codes),
    ).all()
    by_code = {skill.canonical_skill_id: skill for skill in skills}
    if any(code not in by_code for code in configured_codes):
        return PromotionGateState(False, False, None, None, tuple(skill.id for skill in skills), configured_codes)

    critical_ids = tuple(by_code[code].id for code in configured_codes)
    latest_by_skill: dict[int, float] = {}
    for signal in signals:
        latest_by_skill[signal.skill_id] = signal.score

    coverage_ok = all(skill_id in latest_by_skill for skill_id in critical_ids)
    available_scores = {
        skill_id: latest_by_skill[skill_id]
        for skill_id in critical_ids
        if skill_id in latest_by_skill
    }
    weakest_skill_id = min(available_scores, key=available_scores.get) if available_scores else None
    minimum = min(available_scores.values()) if coverage_ok and available_scores else None
    return PromotionGateState(True, coverage_ok, minimum, weakest_skill_id, critical_ids, configured_codes)


def _reinforcement_gate_state(
    db: Session,
    student_id: int,
    level_id: int,
    session_id: int | None = None,
) -> tuple[bool, bool]:
    query = (
        db.query(ReinforcementCycle)
        .join(AssessmentSession, AssessmentSession.id == ReinforcementCycle.session_id)
        .filter(
            ReinforcementCycle.student_id == student_id,
            AssessmentSession.assigned_level == level_id,
        )
    )
    if session_id is not None:
        query = query.filter(ReinforcementCycle.session_id == session_id)
    rows = query.all()
    unresolved = any(
        row.status in {"reinforcement_pending", "reinforcement_in_progress", "verification_pending"}
        for row in rows
    )
    supervisor_review = any(row.status == "escalated" for row in rows)
    return unresolved, supervisor_review


def _weakest_observed_skill(signals: list[AttemptSignal]) -> Optional[int]:
    latest_by_skill: dict[int, float] = {}
    for signal in signals:
        latest_by_skill[signal.skill_id] = signal.score
    return min(latest_by_skill, key=latest_by_skill.get) if latest_by_skill else None


def _recommended_reinforcement(
    db: Session,
    student_id: int,
    level_id: int,
    weakest_skill_id: Optional[int],
) -> Optional[int]:
    reviewed = recommended_reinforcement_for_skill(
        db,
        student_id=student_id,
        level_id=level_id,
        weakest_skill_id=weakest_skill_id,
    )
    if reviewed is not None:
        return reviewed
    if weakest_skill_id is None:
        return None

    used = {
        row[0]
        for row in db.query(Attempt.item_id)
        .join(AssessmentSession, AssessmentSession.id == Attempt.session_id)
        .join(ContentItem, ContentItem.id == Attempt.item_id)
        .filter(
            AssessmentSession.student_id == student_id,
            ContentItem.kind == "reinforcement_activity",
            ContentItem.level_id == level_id,
        )
        .all()
    }
    query = db.query(ContentItem).filter(
        ContentItem.kind == "reinforcement_activity",
        ContentItem.level_id == level_id,
        ContentItem.skill_id == weakest_skill_id,
        ContentItem.status == "approved",
    )
    if used:
        query = query.filter(ContentItem.id.notin_(used))
    item = query.order_by(ContentItem.order_index, ContentItem.id).first()
    return item.id if item else None


def _stars_for_attempt(db: Session, attempt: Attempt) -> tuple[int, dict]:
    structured = db.query(ActivityStepResponse).filter(
        ActivityStepResponse.attempt_id == attempt.id,
    ).order_by(ActivityStepResponse.step_id, ActivityStepResponse.attempt_no).all()
    hints = any(row.hint_used for row in structured)
    by_step: dict[int, list[ActivityStepResponse]] = {}
    for row in structured:
        by_step.setdefault(row.step_id, []).append(row)
    retries = any(len(rows) > 1 for rows in by_step.values())

    if not retries and not hints:
        stars, reason = 3, "completed_without_help"
    elif retries:
        stars, reason = 1, "completed_after_retries"
    else:
        stars, reason = 2, "completed_with_help_without_retry"
    return stars, {"reason": reason, "retry_used": retries, "hint_used": hints}


def _add_reward_once(db: Session, reward: RewardEvent) -> bool:
    try:
        with db.begin_nested():
            db.add(reward)
            db.flush()
        return True
    except IntegrityError:
        return False


def ensure_rewards(db: Session, student_id: int) -> list[RewardEvent]:
    completed = (
        db.query(Attempt, ContentItem, AssessmentSession)
        .join(ContentItem, ContentItem.id == Attempt.item_id)
        .join(AssessmentSession, AssessmentSession.id == Attempt.session_id)
        .filter(
            AssessmentSession.student_id == student_id,
            Attempt.status == "completed",
            ContentItem.kind.in_(["core_activity", "reinforcement_activity"]),
        )
        .order_by(Attempt.id)
        .all()
    )
    changed = False
    for attempt, item, session in completed:
        if _attempt_signal(db, attempt, item) is None:
            continue
        key = f"activity:{attempt.id}:stars"
        exists = db.query(RewardEvent.id).filter(
            RewardEvent.student_id == student_id,
            RewardEvent.reward_key == key,
        ).first()
        if not exists:
            stars, details = _stars_for_attempt(db, attempt)
            changed = _add_reward_once(
                db,
                RewardEvent(
                    student_id=student_id,
                    attempt_id=attempt.id,
                    reward_type="stars",
                    reward_key=key,
                    stars=stars,
                    label=f"{stars} من 3",
                    details={**details, "item_id": item.id, "level_id": item.level_id},
                ),
            ) or changed

    for level_id, label in BADGE_BY_LEVEL.items():
        if not _core_flow_complete(db, student_id, level_id):
            continue
        key = f"level:{level_id}:core-complete"
        if not db.query(RewardEvent.id).filter(
            RewardEvent.student_id == student_id,
            RewardEvent.reward_key == key,
        ).first():
            changed = _add_reward_once(
                db,
                RewardEvent(
                    student_id=student_id,
                    attempt_id=None,
                    reward_type="badge",
                    reward_key=key,
                    stars=None,
                    label=label,
                    details={"event": "level_core_flow_completed", "level_id": level_id},
                ),
            ) or changed

    if changed:
        db.commit()
    return db.query(RewardEvent).filter(
        RewardEvent.student_id == student_id,
    ).order_by(RewardEvent.id).all()


def _previous_automatic_decision_same_level(
    db: Session,
    student_id: int,
    level_id: int,
) -> Optional[AdaptationDecision]:
    return (
        db.query(AdaptationDecision)
        .filter(
            AdaptationDecision.student_id == student_id,
            AdaptationDecision.decision_source == "automatic",
            AdaptationDecision.previous_level == level_id,
            AdaptationDecision.new_level == level_id,
        )
        .order_by(AdaptationDecision.id.desc())
        .first()
    )


def evaluate_student(
    db: Session,
    student: Student,
    session_id: int | None = None,
) -> dict:
    ensure_rewards(db, student.id)
    level_id = student.current_level

    if session_id is not None:
        scoped_session = db.query(AssessmentSession.id).filter(
            AssessmentSession.id == session_id,
            AssessmentSession.student_id == student.id,
            AssessmentSession.session_type == "core",
            AssessmentSession.assigned_level == level_id,
        ).first()
        if scoped_session is None:
            return {
                "ready": False,
                "action": "hold",
                "current_level": level_id,
                "valid_attempt_count": 0,
                "required_attempt_count": 3,
                "completed_core_count": 0,
                "evidence_scope_session_id": session_id,
                "reason": "active_session_level_mismatch",
            }

    signals = _valid_signals(db, student.id, level_id, session_id=session_id)
    completed_core_count = _completed_core_count(db, student.id, level_id, session_id=session_id)

    if len(signals) < 3:
        if signals and signals[-1].score < REINFORCEMENT_THRESHOLD:
            latest = signals[-1]
            snapshot_key = f"immediate:{latest.attempt_id}"
            existing = db.query(AdaptationDecision).filter(
                AdaptationDecision.student_id == student.id,
                AdaptationDecision.decision_source == "automatic",
                AdaptationDecision.snapshot_key == snapshot_key,
            ).first()
            if existing and existing.action != "demote":
                return _decision_payload(existing)

            recommended_item_id = _recommended_reinforcement(db, student.id, level_id, latest.skill_id)
            decision = AdaptationDecision(
                student_id=student.id,
                decision_source="automatic",
                action="support",
                mastery_score=Decimal(str(latest.score)),
                previous_level=level_id,
                new_level=level_id,
                weakest_skill_id=latest.skill_id,
                recommended_item_id=recommended_item_id,
                valid_attempt_count=len(signals),
                consecutive_low_count=0,
                snapshot_key=snapshot_key,
                explanation={
                    "policy_version": POLICY_VERSION,
                    "decision_scope": "immediate_activity_reinforcement",
                    "evidence_scope_session_id": session_id,
                    "latest_activity_score": latest.score,
                    "reinforcement_threshold": REINFORCEMENT_THRESHOLD,
                    "automatic_demotion": False,
                    "reinforcement_assignment": "reviewed_or_exact_approved_mapping" if recommended_item_id else None,
                    "reason": "activity_below_reinforcement_threshold",
                },
            )
            db.add(decision)
            db.commit()
            db.refresh(decision)
            return _decision_payload(decision)

        return {
            "ready": False,
            "action": "hold",
            "current_level": level_id,
            "valid_attempt_count": len(signals),
            "required_attempt_count": 3,
            "completed_core_count": completed_core_count,
            "evidence_scope_session_id": session_id,
            "reason": "waiting_for_three_valid_attempts",
        }

    latest = list(reversed(signals[-3:]))
    snapshot_key = ":".join(str(signal.attempt_id) for signal in latest)
    existing = db.query(AdaptationDecision).filter(
        AdaptationDecision.student_id == student.id,
        AdaptationDecision.decision_source == "automatic",
        AdaptationDecision.snapshot_key == snapshot_key,
    ).first()
    if existing and existing.action != "demote" and (existing.explanation or {}).get("policy_version") == POLICY_VERSION:
        return _decision_payload(existing)

    mastery = weighted_mastery([signal.score for signal in latest])
    gate = _critical_skill_gate_state(db, level_id, signals)
    unresolved_reinforcement, supervisor_review_pending = _reinforcement_gate_state(
        db, student.id, level_id, session_id=session_id
    )
    weakest_skill_id = gate.weakest_skill_id or _weakest_observed_skill(signals)

    previous = _previous_automatic_decision_same_level(db, student.id, level_id)
    previous_low = bool(
        previous
        and previous.mastery_score is not None
        and float(previous.mastery_score) < SUPPORT_THRESHOLD
        and previous.consecutive_low_count >= 1
    )

    action, new_level, reason = decide_transition(
        current_level=level_id,
        mastery=mastery,
        skill_coverage_ok=gate.coverage_ok,
        minimum_required_skill_score=gate.minimum_score,
        previous_low=previous_low,
        completed_core_count=completed_core_count,
        unresolved_reinforcement=unresolved_reinforcement,
        supervisor_review_pending=supervisor_review_pending,
        critical_policy_configured=gate.configured,
    )

    latest_signal = latest[0]
    if action == "stay" and latest_signal.score < REINFORCEMENT_THRESHOLD and not supervisor_review_pending:
        action = "support"
        new_level = level_id
        reason = "activity_below_reinforcement_threshold"
        weakest_skill_id = latest_signal.skill_id

    low_count = (
        (int(previous.consecutive_low_count) + 1 if previous_low else 1)
        if mastery < SUPPORT_THRESHOLD
        else 0
    )

    recommended_item_id = None
    if action == "support":
        recommended_item_id = _recommended_reinforcement(db, student.id, level_id, weakest_skill_id)

    explanation = {
        "policy_version": POLICY_VERSION,
        "pilot_policy": True,
        "evidence_scope_session_id": session_id,
        "weights_newest_to_oldest": list(WEIGHTS),
        "attempts_newest_to_oldest": [
            {"attempt_id": signal.attempt_id, "skill_id": signal.skill_id, "score": signal.score}
            for signal in latest
        ],
        "latest_activity_score": latest_signal.score,
        "completed_core_count": completed_core_count,
        "minimum_core_for_early_promotion": EARLY_PROMOTION_MIN_CORE,
        "critical_skill_policy_configured": gate.configured,
        "critical_skill_codes": list(gate.critical_skill_codes),
        "critical_skill_coverage_ok": gate.coverage_ok,
        "minimum_critical_skill_score": gate.minimum_score,
        "critical_skill_floor": CRITICAL_SKILL_FLOOR,
        "promotion_threshold": PROMOTION_THRESHOLD,
        "support_threshold": SUPPORT_THRESHOLD,
        "reinforcement_threshold": REINFORCEMENT_THRESHOLD,
        "unresolved_reinforcement": unresolved_reinforcement,
        "supervisor_review_pending": supervisor_review_pending,
        "previous_low_same_level": previous_low,
        "automatic_demotion": False,
        "reinforcement_assignment": "reviewed_or_exact_approved_mapping" if recommended_item_id else None,
        "reason": reason,
    }
    decision = AdaptationDecision(
        student_id=student.id,
        decision_source="automatic",
        action=action,
        mastery_score=Decimal(str(mastery)),
        previous_level=level_id,
        new_level=new_level,
        weakest_skill_id=weakest_skill_id,
        recommended_item_id=recommended_item_id,
        valid_attempt_count=len(signals),
        consecutive_low_count=low_count,
        snapshot_key=snapshot_key,
        explanation=explanation,
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return _decision_payload(decision)


def _decision_payload(decision: AdaptationDecision) -> dict:
    return {
        "ready": True,
        "decision_id": decision.id,
        "source": decision.decision_source,
        "action": decision.action,
        "mastery_score": float(decision.mastery_score) if decision.mastery_score is not None else None,
        "previous_level": decision.previous_level,
        "new_level": decision.new_level,
        "weakest_skill_id": decision.weakest_skill_id,
        "recommended_item_id": decision.recommended_item_id,
        "valid_attempt_count": decision.valid_attempt_count,
        "consecutive_low_count": decision.consecutive_low_count,
        "explanation": decision.explanation,
        "manual_reason": decision.manual_reason,
        "created_at": decision.created_at,
    }


def _reward_payload(reward: RewardEvent) -> dict:
    return {
        "id": reward.id,
        "type": reward.reward_type,
        "key": reward.reward_key,
        "stars": reward.stars,
        "label": reward.label,
        "details": reward.details,
        "created_at": reward.created_at,
    }


@router.get("/adaptation/status")
def adaptation_status(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    active = (
        db.query(AssessmentSession)
        .filter(
            AssessmentSession.student_id == student.id,
            AssessmentSession.session_type == "core",
            AssessmentSession.status == "in_progress",
            AssessmentSession.assigned_level == student.current_level,
        )
        .order_by(AssessmentSession.id.desc())
        .first()
    )
    return evaluate_student(db, student, session_id=active.id if active else None)


@router.get("/rewards")
def student_rewards(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return [_reward_payload(row) for row in ensure_rewards(db, student.id)]


@router.get("/researcher/students/{student_id}/adaptation/history")
def researcher_adaptation_history(
    student_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")
    return [
        _decision_payload(row)
        for row in db.query(AdaptationDecision)
        .filter(AdaptationDecision.student_id == student_id)
        .order_by(AdaptationDecision.id)
        .all()
    ]


@router.get("/researcher/students/{student_id}/rewards")
def researcher_rewards(
    student_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")
    return [_reward_payload(row) for row in ensure_rewards(db, student_id)]


@router.post("/researcher/students/{student_id}/adaptation/manual-override")
def manual_override(
    student_id: int,
    body: ManualOverrideRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Apply a supervisor override while preserving the longitudinal study path."""
    student = db.query(Student).filter(Student.id == student_id).with_for_update().first()
    if not student:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")

    previous_level = student.current_level
    level_changing = body.new_level != previous_level

    completed_posttest = db.query(AssessmentSession.id).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.session_type == "posttest",
        AssessmentSession.status == "completed",
    ).first()
    if level_changing and completed_posttest:
        raise HTTPException(
            status_code=409,
            detail="لا يمكن تغيير المستوى بعد اعتماد الاختبار البعدي النهائي",
        )

    active_assessment = db.query(AssessmentSession.id).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.session_type.in_(["pretest", "posttest"]),
        AssessmentSession.status == "in_progress",
    ).first()
    if level_changing and active_assessment:
        raise HTTPException(
            status_code=409,
            detail="لا يمكن تغيير المستوى أثناء وجود اختبار نشط",
        )

    active_core_sessions = (
        db.query(AssessmentSession)
        .filter(
            AssessmentSession.student_id == student.id,
            AssessmentSession.session_type == "core",
            AssessmentSession.status == "in_progress",
        )
        .order_by(AssessmentSession.id)
        .all()
    )
    if len(active_core_sessions) > 1:
        raise HTTPException(
            status_code=409,
            detail="توجد أكثر من جلسة تعلم نشطة وتحتاج الحالة إلى مراجعة قبل تغيير المستوى",
        )
    active_core = active_core_sessions[0] if active_core_sessions else None
    if active_core and active_core.assigned_level != previous_level:
        raise HTTPException(
            status_code=409,
            detail="حالة جلسة التعلم لا تطابق المستوى الحالي وتحتاج مراجعة قبل التجاوز",
        )

    has_core_history = db.query(AssessmentSession.id).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.session_type == "core",
    ).first() is not None

    next_session = None
    if level_changing and active_core is not None:
        pending_audio = (
            db.query(AudioSubmission.id)
            .join(AttemptResponse, AttemptResponse.id == AudioSubmission.response_id)
            .join(Attempt, Attempt.id == AttemptResponse.attempt_id)
            .filter(
                Attempt.session_id == active_core.id,
                AudioSubmission.status.in_(["pending", "uploaded", "rerecord_required"]),
            )
            .first()
        )
        unresolved_cycle = db.query(ReinforcementCycle.id).filter(
            ReinforcementCycle.session_id == active_core.id,
            ReinforcementCycle.status.in_([
                "reinforcement_pending",
                "reinforcement_in_progress",
                "verification_pending",
                "escalated",
            ]),
        ).first()
        if pending_audio or unresolved_cycle:
            raise HTTPException(
                status_code=409,
                detail="أكمل مراجعة الصوت أو دورة التقوية المعلقة قبل تغيير المستوى يدويًا",
            )

        now = datetime.now(timezone.utc)
        active_core.status = "completed"
        active_core.completed_at = active_core.completed_at or now
        active_core.updated_at = now
        db.flush()

    if level_changing and has_core_history:
        next_session = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="in_progress",
            assigned_level=body.new_level,
        )
        db.add(next_session)
        student.posttest_enabled = False
        student.posttest_enabled_at = None
        student.posttest_enabled_by = None
        db.flush()

    explanation = {
        "policy_version": POLICY_VERSION,
        "reason": "supervisor_manual_override",
        "automatic_demotion": False,
        "history_preserved": True,
        "level_changed": level_changing,
    }
    if next_session is not None:
        explanation.update({
            "learning_reopened": True,
            "manual_session_transition": True,
            "previous_session_id": active_core.id if active_core is not None else None,
            "next_session_id": next_session.id,
            "posttest_access_reset": True,
        })

    decision = AdaptationDecision(
        student_id=student.id,
        decision_source="manual",
        action="override",
        mastery_score=None,
        previous_level=previous_level,
        new_level=body.new_level,
        weakest_skill_id=None,
        recommended_item_id=None,
        valid_attempt_count=0,
        consecutive_low_count=0,
        snapshot_key=None,
        explanation=explanation,
        manual_reason=body.reason.strip(),
        actor_id=user.id,
    )
    student.current_level = body.new_level
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return _decision_payload(decision)
