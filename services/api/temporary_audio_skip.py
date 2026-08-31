"""Temporary neutral bypass and authoritative pre/post completion policy.

Voice skipping remains a testing-only feature.  This router is registered before
the legacy assessment finish route and therefore owns the current pre/post
completion contract.

M01 source-of-truth rules:

* readiness = 10 items / 20 points;
* word building and reading = 12 items / 40 points;
* fluency and comprehension = 8 items / 40 points;
* readiness below 12/20 forces L1;
* 50..79.99 is L2;
* L3 additionally requires approved word-reading and text-accuracy gates.

The approved client source does not currently provide numeric thresholds for the
last two L3 gates.  The runtime therefore records a provisional L2 placement for
an otherwise >=80 result instead of inventing thresholds.  Neutral audio/media
evidence is excluded from the academic denominator and makes the result
provisional rather than wrong.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import assessment
from content_runtime import canonical_interaction
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
from runtime_flags import temporary_audio_skip_enabled

router = APIRouter(tags=["Temporary audio testing"])

SECTION_WEIGHTS = {
    "readiness": Decimal("20"),
    "word_building": Decimal("40"),
    "fluency_comprehension": Decimal("40"),
}
SECTION_ID_BY_NAME = {
    "readiness": 1,
    "word_building": 2,
    "fluency_comprehension": 3,
}


class TemporaryAudioSkipRequest(BaseModel):
    step_id: int
    elapsed_seconds: int = Field(default=0, ge=0, le=3600)


def _operation(session_id: int, item_id: int, step_id: int) -> str:
    return f"temporary_audio_skip:{session_id}:{item_id}:{step_id}"


def _temporary_skip_markers(db: Session, student_id: int, session_id: int) -> set[tuple[int, int]]:
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


@router.get("/runtime-flags")
def runtime_flags():
    return {
        "temporary_audio_skip": temporary_audio_skip_enabled(),
        "temporary_audio_skip_label": "تخطي مؤقتًا",
    }


@router.post("/temporary-audio/session/{session_id}/attempt/{item_id}/skip")
def skip_recording_task(
    session_id: int,
    item_id: int,
    body: TemporaryAudioSkipRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    if not temporary_audio_skip_enabled():
        raise HTTPException(status_code=403, detail="التخطي المؤقت للتسجيل غير مفعّل")

    idempotency_key = assessment._validate_idempotency_key(idempotency_key)
    operation = _operation(session_id, item_id, body.step_id)
    request_hash = assessment._request_hash(body.model_dump(mode="json"))
    replay = assessment._idempotency_replay(db, student.id, operation, idempotency_key, request_hash)
    if replay is not None:
        return replay

    session = assessment._session_for_student(db, session_id, student.id)
    attempt = db.query(Attempt).filter(
        Attempt.session_id == session.id,
        Attempt.item_id == item_id,
        Attempt.status == "in_progress",
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="لا توجد محاولة تسجيل نشطة لهذه المهمة")

    item = assessment._load_item(db, item_id)
    step = next((candidate for candidate in (item.steps if item else []) if candidate.id == body.step_id), None)
    if not item or not step:
        raise HTTPException(status_code=400, detail="مهمة التسجيل أو خطوتها غير صالحة")
    if canonical_interaction(item) not in assessment.AUDIO_INTERACTIONS:
        raise HTTPException(status_code=400, detail="التخطي المؤقت متاح لمهام التسجيل فقط")

    existing_response = db.query(AttemptResponse).filter(
        AttemptResponse.attempt_id == attempt.id,
        AttemptResponse.step_id == step.id,
    ).first()
    existing_structured = db.query(ActivityStepResponse.id).filter(
        ActivityStepResponse.attempt_id == attempt.id,
        ActivityStepResponse.step_id == step.id,
    ).first()
    if existing_response or existing_structured:
        raise HTTPException(status_code=409, detail="تم إكمال هذه المهمة مسبقًا")

    # TEMPORARY — remove/disable when production audio pipeline is activated.
    # None is a neutral sentinel; no fake recording, score, MinIO object, review,
    # reward or mastery evidence is created.
    db.add(AttemptResponse(
        attempt_id=attempt.id,
        step_id=step.id,
        selected_option_id=None,
        is_correct=None,
        elapsed_seconds=body.elapsed_seconds,
    ))
    db.flush()

    if assessment._completed_response_count(db, attempt.id) >= len(item.steps):
        attempt.status = "completed"
        attempt.completed_at = datetime.now(timezone.utc)
    attempt.elapsed_seconds += body.elapsed_seconds
    session.elapsed_seconds += body.elapsed_seconds
    session.updated_at = datetime.now(timezone.utc)

    response_json = {
        "status": "ok",
        "is_correct": None,
        "temporary_audio_skip": True,
        "academically_neutral": True,
    }
    assessment._store_idempotency(db, student.id, operation, idempotency_key, request_hash, response_json)
    return assessment._commit_idempotent(
        db, student.id, operation, idempotency_key, request_hash, response_json
    )


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


def _attempt_score(
    db: Session,
    attempt: Attempt,
    temporary_markers: set[tuple[int, int]],
) -> tuple[Decimal | None, bool, int]:
    """Return (0..1 score, has_real_audio_evidence, neutral_skip_count)."""
    earned = Decimal("0")
    units = Decimal("0")
    has_audio_evidence = False
    neutral_skips = 0

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

        if (attempt.item_id, response.step_id) in temporary_markers and response.is_correct is None:
            neutral_skips += 1
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
            neutral_skips += 1
            continue
        units += Decimal("1")
        if response.is_correct:
            earned += Decimal("1")

    if units <= 0:
        return None, has_audio_evidence, neutral_skips
    return earned / units, has_audio_evidence, neutral_skips


def _preflight_audio_state(db: Session, session_id: int) -> None:
    """Surface actionable audio-review states before generic completeness errors."""
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


def _score_assessment(
    db: Session,
    student: Student,
    session: AssessmentSession,
) -> dict:
    _preflight_audio_state(db, session.id)

    required_kind = assessment.KIND_BY_SESSION_TYPE[session.session_type]
    required_items = db.query(ContentItem).filter(ContentItem.kind == required_kind).count()
    attempts = db.query(Attempt).filter(Attempt.session_id == session.id).all()
    if required_items != 30 or len(attempts) != required_items or any(a.status != "completed" for a in attempts):
        raise HTTPException(status_code=400, detail="أكمل الأسئلة الثلاثين قبل إنهاء الاختبار")

    markers = _temporary_skip_markers(db, student.id, session.id)
    evidence: list[AssessmentEvidence] = []
    real_audio_evidence = 0
    neutral_skip_count = 0

    for attempt in attempts:
        item = db.query(ContentItem).filter(ContentItem.id == attempt.item_id).first()
        if not item:
            raise HTTPException(status_code=409, detail="تعذر تحميل أحد أسئلة الاختبار")
        item_score, has_audio, skips = _attempt_score(db, attempt, markers)
        real_audio_evidence += int(has_audio)
        neutral_skip_count += skips
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
        "neutral_skip_count": neutral_skip_count,
        "scorable_items": sum(section.valid_items for section in assessment_score.sections.values()),
        "provisional_reasons": list(assessment_score.provisional_reasons),
    }


def _pretest_placement(scored: dict) -> tuple[int, str, bool]:
    """Return the source-grounded placement without manufacturing L3 gates."""
    decision = decide_initial_placement(scored["assessment_score"])
    return decision.assigned_level, decision.reason, decision.status == "provisional"


def _finish_session_with_journey_scoring(db: Session, student: Student, session: AssessmentSession) -> dict:
    if session.session_type not in {"pretest", "posttest"}:
        return assessment.finish_session(session_id=session.id, db=db, student=student)

    scored = _score_assessment(db, student, session)
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
        # Posttest measures outcome; it must never move the student backwards or
        # rewrite the learning journey. Keep assigned_level as journey context.
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
        "temporary_audio_skips": scored["neutral_skip_count"],
        "scorable_items": scored["scorable_items"],
        "scorable_units": scored["scorable_items"],
    }


# Registered before assessment.router in main.py, making this the single
# authoritative pre/post completion endpoint for both normal and temporary-skip
# runs. Other assessment routes remain unchanged.
@router.post("/assessment/session/{session_id}/finish")
def finish_assessment_with_optional_temporary_skips(
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
    return _finish_session_with_journey_scoring(db, student, session)
