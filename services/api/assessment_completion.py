"""Authoritative pre/post assessment completion and placement scoring.

This module owns the permanent completion contract. Historical neutral markers
may still be recognised for compatibility, but there is no active student audio
bypass route and neutral evidence is never converted into academic failure.

Current source-grounded assessment contract:
- readiness = 10 items / 20 points;
- word building and reading = 12 items / 40 points;
- fluency and comprehension = 8 items / 40 points;
- final pretest total <50 starts at L1;
- 50..<80 starts at L2;
- >=80 starts at L3.

Continuous-learning adaptation is a separate V4 policy (80/70 per-activity,
three valid signals weighted 50/30/20, 6-Core/85/70 promotion gates, no
automatic demotion). It must not be mixed into initial placement.

Any uploaded or rerecord-required assessment audio blocks completion until the
supervisor review is resolved. Neutral historical/media-gap evidence is
excluded from the academic denominator and makes the score provisional rather
than incorrect.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import assessment
from db.activity_models import ActivityStepResponse
from db.models import (
    AssessmentSession,
    Attempt,
    AttemptResponse,
    AudioReview,
    AudioSubmission,
    ContentItem,
    OperationIdempotency,
    Student,
)
from dependencies import get_current_student, get_db
from placement_scoring import AssessmentEvidence, decide_initial_placement, score_assessment

router = APIRouter(tags=["Assessment completion"])

SECTION_ID_BY_NAME = {
    "readiness": 1,
    "word_building": 2,
    "fluency_comprehension": 3,
}


def _neutral_development_markers(db: Session, student_id: int, session_id: int) -> set[tuple[int, int]]:
    """Read historical neutral markers without exposing an active bypass."""
    rows = db.query(OperationIdempotency).filter(
        OperationIdempotency.actor_role == "student",
        OperationIdempotency.actor_id == student_id,
        OperationIdempotency.operation.like(f"temporary_audio_skip:{session_id}:%"),
    ).all()
    markers: set[tuple[int, int]] = set()
    for row in rows:
        parts = row.operation.split(":")
        if len(parts) != 4:
            continue
        try:
            markers.add((int(parts[2]), int(parts[3])))
        except ValueError:
            continue
    return markers


def _section_name(order_index: int) -> str:
    if order_index <= 10:
        return "readiness"
    if order_index <= 22:
        return "word_building"
    return "fluency_comprehension"


def _section_id(item: ContentItem) -> int:
    """Prefer catalog level_id because it is the authoritative assessment section."""
    if item.level_id in {1, 2, 3}:
        return int(item.level_id)
    return SECTION_ID_BY_NAME[_section_name(item.order_index)]


def _preflight_audio_state(db: Session, session_id: int) -> None:
    """Surface actionable review states before generic completeness errors."""
    submissions = (
        db.query(AudioSubmission)
        .join(AttemptResponse, AttemptResponse.id == AudioSubmission.response_id)
        .join(Attempt, Attempt.id == AttemptResponse.attempt_id)
        .filter(Attempt.session_id == session_id)
        .all()
    )
    for submission in submissions:
        if submission.status == "rerecord_required":
            raise HTTPException(status_code=409, detail="يوجد تسجيل يحتاج إلى إعادة قبل إنهاء الاختبار")
        if submission.status == "uploaded":
            raise HTTPException(status_code=409, detail="يوجد تسجيل صوتي في انتظار المراجعة")
        if submission.status == "graded":
            review = db.query(AudioReview).filter(
                AudioReview.submission_id == submission.id,
            ).order_by(AudioReview.id.desc()).first()
            if not review:
                raise HTTPException(status_code=409, detail="تقييم التسجيل الصوتي غير مكتمل")


def _attempt_score(
    db: Session,
    attempt: Attempt,
    neutral_markers: set[tuple[int, int]],
) -> tuple[Decimal | None, bool, int]:
    """Return (0..1 score, has real audio evidence, neutral evidence count)."""
    earned = Decimal("0")
    units = Decimal("0")
    has_audio_evidence = False
    neutral_count = 0

    for response in db.query(AttemptResponse).filter(AttemptResponse.attempt_id == attempt.id).all():
        audio_sub = db.query(AudioSubmission).filter(AudioSubmission.response_id == response.id).first()
        if audio_sub:
            if audio_sub.status == "rerecord_required":
                raise HTTPException(status_code=409, detail="يوجد تسجيل يحتاج إلى إعادة قبل إنهاء الاختبار")
            if audio_sub.status == "uploaded":
                raise HTTPException(status_code=409, detail="يوجد تسجيل صوتي في انتظار المراجعة")
            if audio_sub.status == "graded":
                review = db.query(AudioReview).filter(
                    AudioReview.submission_id == audio_sub.id,
                ).order_by(AudioReview.id.desc()).first()
                if not review:
                    raise HTTPException(status_code=409, detail="تقييم التسجيل الصوتي غير مكتمل")
                units += Decimal("1")
                earned += Decimal(str(review.rubric_score))
                has_audio_evidence = True
                continue

        if (attempt.item_id, response.step_id) in neutral_markers and response.is_correct is None:
            neutral_count += 1
            continue
        if response.is_correct is None:
            raise HTTPException(status_code=409, detail="يوجد سؤال غير مكتمل التقييم")
        units += Decimal("1")
        if response.is_correct:
            earned += Decimal("1")

    for response in db.query(ActivityStepResponse).filter(
        ActivityStepResponse.attempt_id == attempt.id,
    ).all():
        payload = response.response_payload or {}
        if payload.get("declared_media_gap_skip") or payload.get("temporary_audio_skip"):
            neutral_count += 1
            continue
        units += Decimal("1")
        if response.is_correct:
            earned += Decimal("1")

    if units <= 0:
        return None, has_audio_evidence, neutral_count
    return earned / units, has_audio_evidence, neutral_count


def score_session(db: Session, student: Student, session: AssessmentSession) -> dict:
    """Build the source-grounded assessment score from persisted evidence only."""
    if session.session_type not in {"pretest", "posttest"}:
        raise HTTPException(status_code=400, detail="هذا المسار مخصص لإنهاء الاختبار القبلي أو البعدي فقط")

    _preflight_audio_state(db, session.id)

    required_kind = assessment.KIND_BY_SESSION_TYPE[session.session_type]
    required_items = db.query(ContentItem).filter(ContentItem.kind == required_kind).count()
    attempts = db.query(Attempt).filter(Attempt.session_id == session.id).all()
    if required_items != 30 or len(attempts) != required_items or any(a.status != "completed" for a in attempts):
        raise HTTPException(status_code=400, detail="أكمل الأسئلة الثلاثين قبل إنهاء الاختبار")

    neutral_markers = _neutral_development_markers(db, student.id, session.id)
    evidence: list[AssessmentEvidence] = []
    real_audio_evidence = 0
    neutral_count = 0

    for attempt in attempts:
        item = db.query(ContentItem).filter(ContentItem.id == attempt.item_id).first()
        if not item:
            raise HTTPException(status_code=409, detail="تعذر تحميل أحد أسئلة الاختبار")
        item_score, has_audio, neutral = _attempt_score(db, attempt, neutral_markers)
        real_audio_evidence += int(has_audio)
        neutral_count += neutral
        evidence.append(AssessmentEvidence(section_id=_section_id(item), score=item_score))

    assessment_score = score_assessment(evidence)
    section_points = {
        "readiness": assessment_score.sections[1].points,
        "word_building": assessment_score.sections[2].points,
        "fluency_comprehension": assessment_score.sections[3].points,
    }
    return {
        "assessment_score": assessment_score,
        "final_percentage": assessment_score.total_points,
        "section_points": section_points,
        "readiness_points": assessment_score.sections[1].points,
        "real_audio_evidence": real_audio_evidence,
        "neutral_count": neutral_count,
        "scorable_items": sum(section.valid_items for section in assessment_score.sections.values()),
        "provisional_reasons": list(assessment_score.provisional_reasons),
    }


def _pretest_placement(scored: dict) -> tuple[int, str, bool]:
    decision = decide_initial_placement(scored["assessment_score"])
    return decision.assigned_level, decision.reason, decision.status == "provisional"


def finish_session(db: Session, student: Student, session: AssessmentSession) -> dict:
    """Finalize pre/post without rewriting learning history or inventing evidence."""
    scored = score_session(db, student, session)
    final_percentage: Decimal = scored["final_percentage"]
    now = datetime.now(timezone.utc)

    placement_reason = None
    provisional = bool(scored["assessment_score"].provisional)
    result_band = 1 if final_percentage < 50 else 2 if final_percentage < 80 else 3

    if session.session_type == "pretest":
        assigned_level, placement_reason, provisional = _pretest_placement(scored)
        student.current_level = assigned_level
        session.assigned_level = assigned_level
    else:
        # Posttest measures outcome. It must not move the learner backwards or
        # rewrite the completed learning journey.
        assigned_level = student.current_level
        session.assigned_level = student.current_level
        student.posttest_enabled = False
        student.posttest_enabled_at = None
        student.posttest_enabled_by = None

    session.final_score = final_percentage
    session.status = "completed"
    session.completed_at = now
    session.updated_at = now
    db.commit()

    return {
        "id": session.id,
        "final_score": final_percentage,
        "assigned_level": assigned_level,
        "result_band": result_band,
        "section_points": {key: float(value) for key, value in scored["section_points"].items()},
        "placement_reason": placement_reason,
        "placement_provisional": provisional,
        "placement_provisional_reasons": scored["provisional_reasons"],
        # Historical response-field compatibility only; there is no active bypass route.
        "temporary_audio_skips": scored["neutral_count"],
        "neutral_evidence_units": scored["neutral_count"],
        "scorable_items": scored["scorable_items"],
        "scorable_units": scored["scorable_items"],
    }


@router.post("/assessment/session/{session_id}/finish")
def finish_assessment(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.student_id == student.id,
    ).first()
    if not session or session.status != "in_progress":
        raise HTTPException(status_code=400, detail="الجلسة غير صالحة أو مكتملة")
    return finish_session(db, student, session)
