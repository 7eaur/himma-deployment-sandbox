"""Student-facing learning journey summary.

This module is presentation-oriented: it exposes the already-persisted academic
state without mutating placement, adaptation, reinforcement, or assessment
rules. The frontend can therefore render L1 -> L2 -> L3 accurately instead of
inferring completion from the latest session only.

An active Core session always takes precedence over older completed evidence at
the same level. This matters when a supervisor deliberately reopens learning:
historical achievements stay visible in storage, but they must not make the
current journey or posttest look complete while remediation is active.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.adaptation_models import AdaptationDecision
from db.models import AssessmentSession, Attempt, ContentItem, Student
from dependencies import get_current_student, get_db

router = APIRouter(prefix="/journey", tags=["Student Journey"])
CORE_ACTIVITY_COUNT = 10

LEVEL_NAMES = {
    1: "الاستعداد للقراءة",
    2: "بناء الكلمة",
    3: "الطلاقة والفهم",
}


def _completed_core_count(db: Session, session_id: int, level_id: int) -> int:
    rows = (
        db.query(ContentItem.id)
        .join(Attempt, Attempt.item_id == ContentItem.id)
        .filter(
            Attempt.session_id == session_id,
            Attempt.status == "completed",
            ContentItem.kind == "core_activity",
            ContentItem.level_id == level_id,
        )
        .distinct()
        .all()
    )
    return len(rows)


def _pretest_state(db: Session, student_id: int) -> tuple[bool, int | None]:
    pretest = (
        db.query(AssessmentSession)
        .filter(
            AssessmentSession.student_id == student_id,
            AssessmentSession.session_type == "pretest",
        )
        .order_by(AssessmentSession.id.desc())
        .first()
    )
    if not pretest or pretest.status != "completed":
        return False, None
    return True, pretest.assigned_level


def _posttest_completed(db: Session, student_id: int) -> bool:
    return (
        db.query(AssessmentSession.id)
        .filter(
            AssessmentSession.student_id == student_id,
            AssessmentSession.session_type == "posttest",
            AssessmentSession.status == "completed",
        )
        .first()
        is not None
    )


def _promotion_closed_session_ids(db: Session, student_id: int) -> set[int]:
    """Return sessions closed by a persisted one-level automatic promotion.

    L1/L2 may legitimately close after the V4 early-promotion gate (six or more
    Core activities). Presentation uses that persisted transition evidence
    rather than re-imposing the legacy ten-Core requirement. L3 is excluded
    because journey completion still requires all ten Core activities.
    """
    session_ids: set[int] = set()
    decisions = (
        db.query(AdaptationDecision)
        .filter(
            AdaptationDecision.student_id == student_id,
            AdaptationDecision.decision_source == "automatic",
            AdaptationDecision.action == "promote",
        )
        .order_by(AdaptationDecision.id)
        .all()
    )
    for decision in decisions:
        if decision.previous_level not in {1, 2} or decision.new_level != decision.previous_level + 1:
            continue
        explanation = decision.explanation or {}
        previous_session_id = explanation.get("previous_session_id")
        expected_transition = f"L{decision.previous_level}->L{decision.new_level}"
        if isinstance(previous_session_id, int) and explanation.get("journey_transition") == expected_transition:
            session_ids.add(previous_session_id)
    return session_ids


def build_journey_summary(db: Session, student: Student) -> dict:
    pretest_completed, placed_level = _pretest_state(db, student.id)
    starting_level = placed_level if placed_level in {1, 2, 3} else (student.current_level if pretest_completed else None)
    promotion_closed_sessions = _promotion_closed_session_ids(db, student.id)

    sessions = (
        db.query(AssessmentSession)
        .filter(
            AssessmentSession.student_id == student.id,
            AssessmentSession.session_type == "core",
        )
        .order_by(AssessmentSession.id)
        .all()
    )
    by_level: dict[int, list[AssessmentSession]] = {1: [], 2: [], 3: []}
    for session in sessions:
        if session.assigned_level in by_level:
            by_level[int(session.assigned_level)].append(session)

    active_core_exists = any(session.status == "in_progress" for session in sessions)
    levels: list[dict] = []
    level3_completed = False

    for level_id in (1, 2, 3):
        candidates = by_level[level_id]
        active = next((session for session in reversed(candidates) if session.status == "in_progress"), None)

        completed_candidates: list[tuple[AssessmentSession, int]] = []
        latest_count = 0
        for session in candidates:
            count = _completed_core_count(db, session.id, level_id)
            if session is candidates[-1]:
                latest_count = count
            completed_by_full_evidence = count >= CORE_ACTIVITY_COUNT
            completed_by_early_promotion = level_id in {1, 2} and session.id in promotion_closed_sessions
            if session.status == "completed" and (completed_by_full_evidence or completed_by_early_promotion):
                completed_candidates.append((session, count))

        completed_entry = completed_candidates[-1] if completed_candidates else None

        if not pretest_completed:
            state = "locked"
            completed_items = 0
            session_id = None
        elif active:
            # A supervisor-reopened/remedial session is the current truth even
            # when an older session at this level was previously completed.
            state = "active"
            completed_items = _completed_core_count(db, active.id, level_id)
            session_id = active.id
        elif completed_entry:
            state = "completed"
            completed_items = completed_entry[1]
            session_id = completed_entry[0].id
        elif starting_level is not None and level_id < starting_level and not candidates:
            # Placement legitimately skipped this level and no later manual
            # intervention ever created real learning evidence here.
            state = "skipped"
            completed_items = 0
            session_id = None
        elif level_id == student.current_level:
            state = "ready"
            completed_items = latest_count
            session_id = candidates[-1].id if candidates else None
        else:
            state = "locked"
            completed_items = latest_count
            session_id = candidates[-1].id if candidates else None

        if level_id == 3 and state == "completed":
            level3_completed = True

        levels.append(
            {
                "level_id": level_id,
                "name": LEVEL_NAMES[level_id],
                "state": state,
                "completed_items": min(CORE_ACTIVITY_COUNT, completed_items),
                "total_items": CORE_ACTIVITY_COUNT,
                "session_id": session_id,
            }
        )

    posttest_completed = _posttest_completed(db, student.id)
    learning_journey_completed = level3_completed and not active_core_exists
    return {
        "pretest_completed": pretest_completed,
        "starting_level": starting_level,
        "current_level": student.current_level,
        "levels": levels,
        "learning_journey_completed": learning_journey_completed,
        "posttest_enabled": bool(student.posttest_enabled),
        "posttest_completed": posttest_completed,
        "posttest_ready": learning_journey_completed and bool(student.posttest_enabled) and not posttest_completed,
    }


@router.get("")
def student_journey(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return build_journey_summary(db, student)
