"""Runtime bridge for the Himma adaptive learning journey.

Each level owns a durable ``core`` session. A level transition closes the active
session and opens a fresh session for the new level without relabelling history.
Reinforcement remains inside the current level. A missing approved mapping
blocks progression and delegates selection to the documented supervisor-review
flow instead of selecting unrelated content.

Automatic demotion is not a valid runtime transition. Historical demotion rows
may remain visible in audit history, but this runtime only executes promotion.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from adaptation import evaluate_student
from db.adaptation_models import AdaptationDecision
from db.models import AssessmentSession, Attempt, ContentItem, Student
from db.reinforcement_models import ReinforcementCycle
from dependencies import get_current_student, get_db
from reinforcement_cycles import ensure_cycle, mark_reinforcement_completed

router = APIRouter(prefix="/adaptation", tags=["Adaptation Runtime"])
CORE_ACTIVITY_COUNT = 10


def _completed_core_count(db: Session, session_id: int, level_id: int) -> int:
    return (
        db.query(Attempt.id)
        .join(ContentItem, ContentItem.id == Attempt.item_id)
        .filter(
            Attempt.session_id == session_id,
            Attempt.status == "completed",
            ContentItem.kind == "core_activity",
            ContentItem.level_id == level_id,
        )
        .count()
    )


def _recommended_attempt(db: Session, session_id: int, item_id: int | None) -> Attempt | None:
    if item_id is None:
        return None
    return (
        db.query(Attempt)
        .filter(Attempt.session_id == session_id, Attempt.item_id == item_id)
        .order_by(Attempt.id.desc())
        .first()
    )


def _recommended_attempt_state(db: Session, session_id: int, item_id: int | None) -> str | None:
    attempt = _recommended_attempt(db, session_id, item_id)
    return attempt.status if attempt else None


def _ensure_recommended_attempt(
    db: Session,
    session: AssessmentSession,
    decision: AdaptationDecision,
) -> int | None:
    """Create only the explicitly approved mapped reinforcement attempt."""
    item_id = decision.recommended_item_id
    if item_id is None or decision.action != "support":
        return None

    item = db.query(ContentItem).filter(ContentItem.id == item_id).first()
    if not item:
        return None
    if (
        item.kind != "reinforcement_activity"
        or item.level_id != decision.previous_level
        or item.status != "approved"
    ):
        raise HTTPException(status_code=409, detail="نشاط التقوية لا يطابق المستوى الحالي")

    existing = _recommended_attempt(db, session.id, item.id)
    if existing:
        return existing.id if existing.status == "in_progress" else None

    attempt = Attempt(session_id=session.id, item_id=item.id, status="in_progress")
    try:
        with db.begin_nested():
            db.add(attempt)
            db.flush()
    except IntegrityError:
        existing = _recommended_attempt(db, session.id, item.id)
        return existing.id if existing and existing.status == "in_progress" else None
    return attempt.id


def _transition_level_session(
    db: Session,
    student: Student,
    old_session: AssessmentSession,
    new_level: int,
) -> AssessmentSession:
    """Close the current level and open a fresh target-level session safely.

    Completed historical target-level sessions are preserved and never reopened.
    A currently active target-level session may only be reused as an idempotent
    recovery/race result.
    """
    if new_level < 1 or new_level > 3:
        raise HTTPException(status_code=409, detail="المستوى الجديد غير صالح")
    if new_level <= old_session.assigned_level:
        raise HTTPException(status_code=409, detail="الانتقال التلقائي يجب أن يكون ترقية فقط")

    now = datetime.now(timezone.utc)
    old_session.status = "completed"
    old_session.completed_at = old_session.completed_at or now
    old_session.updated_at = now
    db.flush()

    active_target = (
        db.query(AssessmentSession)
        .filter(
            AssessmentSession.student_id == student.id,
            AssessmentSession.session_type == "core",
            AssessmentSession.assigned_level == new_level,
            AssessmentSession.status == "in_progress",
        )
        .order_by(AssessmentSession.id.desc())
        .first()
    )
    if active_target:
        student.current_level = new_level
        return active_target

    next_session = AssessmentSession(
        student_id=student.id,
        session_type="core",
        status="in_progress",
        assigned_level=new_level,
    )
    db.add(next_session)
    student.current_level = new_level
    db.flush()
    return next_session


def _existing_cycle_hold(db: Session, session: AssessmentSession) -> dict | None:
    """Keep bounded verification/escalation authoritative over fresh adaptation."""
    cycle = (
        db.query(ReinforcementCycle)
        .filter(
            ReinforcementCycle.session_id == session.id,
            ReinforcementCycle.status.in_(["verification_pending", "escalated"]),
        )
        .order_by(ReinforcementCycle.id.desc())
        .first()
    )
    if cycle is None:
        return None
    if cycle.status == "verification_pending":
        return {
            "continue_learning": True,
            "decision": {"ready": True, "action": "verify_core_after_reinforcement"},
            "recommended_attempt_id": None,
            "verification_attempt_id": cycle.source_attempt_id,
            "mapping_blocked": False,
            "recommendation_fulfilled": True,
            "verification_escalated": False,
            "reinforcement_cycle_id": cycle.id,
            "level_id": session.assigned_level,
            "session_id": session.id,
            "level_transitioned": False,
        }
    return {
        "continue_learning": False,
        "decision": {
            "ready": True,
            "action": "supervisor_hold",
            "reason": cycle.escalation_reason or "reinforcement_verification_escalated",
        },
        "recommended_attempt_id": None,
        "verification_attempt_id": None,
        "mapping_blocked": False,
        "recommendation_fulfilled": True,
        "verification_escalated": True,
        "reinforcement_cycle_id": cycle.id,
        "level_id": session.assigned_level,
        "session_id": session.id,
        "level_transitioned": False,
    }


def prepare_next_for_student(db: Session, student: Student, session: AssessmentSession) -> dict:
    """Evaluate only this active session and prepare the next safe learning action."""
    existing_hold = _existing_cycle_hold(db, session)
    if existing_hold is not None:
        return existing_hold

    decision_payload = evaluate_student(db, student, session_id=session.id)
    if not decision_payload.get("ready"):
        return {
            "continue_learning": session.status == "in_progress",
            "decision": decision_payload,
            "recommended_attempt_id": None,
            "verification_attempt_id": None,
            "mapping_blocked": False,
            "recommendation_fulfilled": False,
            "level_id": session.assigned_level,
            "session_id": session.id,
        }

    decision = db.query(AdaptationDecision).filter(
        AdaptationDecision.id == decision_payload["decision_id"],
    ).one()

    if decision.action == "promote" and decision.new_level > decision.previous_level:
        next_session = _transition_level_session(db, student, session, decision.new_level)
        explanation = dict(decision.explanation or {})
        explanation["journey_transition"] = f"L{decision.previous_level}->L{decision.new_level}"
        explanation["transition_direction"] = "promotion"
        explanation["previous_session_id"] = session.id
        explanation["next_session_id"] = next_session.id
        decision.explanation = explanation
        db.commit()
        return {
            "continue_learning": next_session.status == "in_progress",
            "decision": {**decision_payload, "explanation": decision.explanation},
            "recommended_attempt_id": None,
            "verification_attempt_id": None,
            "mapping_blocked": False,
            "recommendation_fulfilled": False,
            "level_id": decision.new_level,
            "session_id": next_session.id,
            "level_transitioned": True,
            "transition_direction": "promotion",
        }

    # Historical V3 demotion decisions are audit-only and are never executed.
    if decision.action == "demote":
        return {
            "continue_learning": session.status == "in_progress",
            "decision": {
                **decision_payload,
                "action": "support",
                "new_level": session.assigned_level,
                "reason": "historical_demotion_blocked_by_current_policy",
            },
            "recommended_attempt_id": None,
            "verification_attempt_id": None,
            "mapping_blocked": True,
            "recommendation_fulfilled": False,
            "level_id": session.assigned_level,
            "session_id": session.id,
            "level_transitioned": False,
        }

    if (
        decision.previous_level == 3
        and decision.explanation.get("reason") == "top_level_mastery"
        and _completed_core_count(db, session.id, 3) >= CORE_ACTIVITY_COUNT
    ):
        now = datetime.now(timezone.utc)
        session.status = "completed"
        session.completed_at = session.completed_at or now
        session.updated_at = now
        db.commit()
        return {
            "continue_learning": False,
            "decision": decision_payload,
            "recommended_attempt_id": None,
            "verification_attempt_id": None,
            "mapping_blocked": False,
            "recommendation_fulfilled": False,
            "level_id": 3,
            "session_id": session.id,
            "journey_completed": True,
        }

    recommendation_state_before = _recommended_attempt_state(db, session.id, decision.recommended_item_id)
    attempt_id = _ensure_recommended_attempt(db, session, decision)
    reinforcement_attempt = _recommended_attempt(db, session.id, decision.recommended_item_id)
    recommendation_state_after = reinforcement_attempt.status if reinforcement_attempt else None
    recommendation_fulfilled = (
        recommendation_state_before == "completed" or recommendation_state_after == "completed"
    )

    cycle = ensure_cycle(
        db,
        student=student,
        session_id=session.id,
        decision=decision,
        reinforcement_attempt_id=reinforcement_attempt.id if reinforcement_attempt else attempt_id,
    )

    mapping_blocked = (
        decision.action == "support"
        and decision.recommended_item_id is None
        and attempt_id is None
        and not recommendation_fulfilled
    )
    explanation = dict(decision.explanation or {})
    verification_attempt_id = None
    verification_escalated = False

    if mapping_blocked:
        explanation["mapping_gap"] = "no_approved_reinforcement_selected_for_weakest_skill"
        session.status = "in_progress"
        session.completed_at = None
    elif recommendation_fulfilled:
        explanation.pop("mapping_gap", None)
        explanation["mapping_gap_resolved"] = True
        explanation["reinforcement_fulfilled"] = True
        explanation["return_to_core"] = True
        if cycle is not None:
            source_attempt = mark_reinforcement_completed(db, cycle=cycle)
            if source_attempt is not None:
                verification_attempt_id = source_attempt.id
                explanation["reinforcement_cycle_id"] = cycle.id
                explanation["verification_pending"] = True
                explanation["return_to_core_attempt_id"] = source_attempt.id
            elif cycle.status == "escalated":
                verification_escalated = True
                explanation["verification_escalated"] = True
                explanation["verification_escalation_reason"] = cycle.escalation_reason
    decision.explanation = explanation

    if attempt_id is not None and session.status == "completed":
        session.status = "in_progress"
        session.completed_at = None
        session.updated_at = datetime.now(timezone.utc)

    if verification_attempt_id is not None:
        session.status = "in_progress"
        session.completed_at = None
        session.updated_at = datetime.now(timezone.utc)

    db.commit()
    return {
        "continue_learning": session.status == "in_progress" and not verification_escalated,
        "decision": {
            **decision_payload,
            "recommended_item_id": decision.recommended_item_id,
            "explanation": decision.explanation,
        },
        "recommended_attempt_id": attempt_id,
        "verification_attempt_id": verification_attempt_id,
        "mapping_blocked": mapping_blocked,
        "recommendation_fulfilled": recommendation_fulfilled,
        "verification_escalated": verification_escalated,
        "level_id": session.assigned_level,
        "session_id": session.id,
        "level_transitioned": False,
    }


@router.post("/session/{session_id}/prepare-next")
def prepare_adaptive_next(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.student_id == student.id,
        AssessmentSession.session_type == "core",
    ).with_for_update().first()
    if not session:
        raise HTTPException(status_code=404, detail="جلسة التعلم غير موجودة")
    return prepare_next_for_student(db, student, session)
