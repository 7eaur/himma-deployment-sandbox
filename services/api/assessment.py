import hashlib
import json
import re
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from content_runtime import (
    canonical_id,
    canonical_interaction,
    instruction_text,
    item_assets,
    media_gaps,
    semantic_key,
    step_assets,
)
from dependencies import get_db, get_current_student
from db.activity_models import ActivityStepResponse
from db.models import (
    AudioReview,
    AudioSubmission,
    AssessmentSession,
    Attempt,
    AttemptResponse,
    ContentItem,
    ContentOption,
    ContentStep,
    OperationIdempotency,
    Student,
)
import schemas
import storage

router = APIRouter(prefix="/assessment", tags=["Assessment"])

KIND_BY_SESSION_TYPE = {
    "pretest": "pretest_question",
    "posttest": "posttest_question",
}

AUDIO_INTERACTIONS = {"read_aloud", "timed_read_aloud"}
SINGLE_INTERACTIONS = {
    "choose_one",
    "listen_choose_one",
    "choose_image",
    "listen_choose_image",
}
STRUCTURED_INTERACTIONS = {
    "choose_many",
    "listen_choose_many",
    "sequence",
    "memory_sequence",
    "path_sequence",
    "build_word",
}
IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{16,128}$")


class AssessmentAnswerRequest(BaseModel):
    step_id: int
    selected_option_id: Optional[int] = None
    selected_option_ids: list[int] = Field(default_factory=list, max_length=20)
    audio_storage_key: Optional[str] = None
    audio_file_size: Optional[int] = Field(default=None, gt=0)
    audio_mime_type: Optional[str] = None
    audio_duration_seconds: Optional[Decimal] = None
    elapsed_seconds: int = Field(default=0, ge=0, le=3600)


def _validate_idempotency_key(value: str) -> str:
    if not IDEMPOTENCY_KEY_PATTERN.fullmatch(value):
        raise HTTPException(status_code=400, detail="تعذر حفظ المحاولة. أعد تحميل الصفحة وحاول مرة أخرى")
    return value


def _request_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _idempotency_replay(
    db: Session,
    student_id: int,
    operation: str,
    idempotency_key: str,
    request_hash: str,
) -> Optional[dict]:
    record = db.query(OperationIdempotency).filter(
        OperationIdempotency.actor_role == "student",
        OperationIdempotency.actor_id == student_id,
        OperationIdempotency.operation == operation,
        OperationIdempotency.idempotency_key == idempotency_key,
    ).first()
    if not record:
        return None
    if record.request_hash != request_hash:
        raise HTTPException(status_code=409, detail="هذه المحاولة سُجلت مسبقًا ببيانات مختلفة")
    return record.response_json


def _store_idempotency(
    db: Session,
    student_id: int,
    operation: str,
    idempotency_key: str,
    request_hash: str,
    response_json: dict,
) -> None:
    db.add(OperationIdempotency(
        actor_role="student",
        actor_id=student_id,
        operation=operation,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        response_json=response_json,
        status_code=200,
    ))


def _commit_idempotent(
    db: Session,
    student_id: int,
    operation: str,
    idempotency_key: str,
    request_hash: str,
    response_json: dict,
) -> dict:
    try:
        db.commit()
        return response_json
    except IntegrityError:
        db.rollback()
        replay = _idempotency_replay(db, student_id, operation, idempotency_key, request_hash)
        if replay is not None:
            return replay
        raise HTTPException(status_code=409, detail="حدث تعارض أثناء حفظ الإجابة. أعد المحاولة")


def _session_for_student(
    db: Session,
    session_id: int,
    student_id: int,
    *,
    require_active: bool = True,
) -> AssessmentSession:
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.student_id == student_id,
    ).first()
    if not session or (require_active and session.status != "in_progress"):
        raise HTTPException(status_code=404, detail="الجلسة غير موجودة أو انتهت")
    return session


def _load_item(db: Session, item_id: int) -> ContentItem | None:
    return db.query(ContentItem).options(
        joinedload(ContentItem.steps).joinedload(ContentStep.options),
        joinedload(ContentItem.steps).joinedload(ContentStep.assets),
        joinedload(ContentItem.assets),
    ).filter(ContentItem.id == item_id).first()


def _item_step_payload(item: ContentItem, step: ContentStep) -> dict:
    data = item.template_data or {}
    return {
        "id": item.id,
        "stable_key": item.stable_key,
        "canonical_id": canonical_id(item),
        "kind": item.kind,
        "interaction_type": canonical_interaction(item),
        "title": data.get("title") or "مهمة تعليمية",
        "source_method": data.get("source_method"),
        "template_data": item.template_data,
        "item_assets": item_assets(item),
        "steps": [{
            "id": step.id,
            "order_index": step.order_index,
            "prompt_text": step.prompt_text,
            "instruction_text": instruction_text(item, step),
            "expected_reading_text": step.expected_reading_text,
            "options": [
                {"id": option.id, "text": option.text, "order_index": option.order_index}
                for option in step.options
            ],
            "assets": step_assets(item, step),
            "media_gaps": media_gaps(item, step),
        }],
    }


def _structured_response_exists(db: Session, attempt_id: int, step_id: int) -> bool:
    return db.query(ActivityStepResponse.id).filter(
        ActivityStepResponse.attempt_id == attempt_id,
        ActivityStepResponse.step_id == step_id,
    ).first() is not None


def _answered_step_ids(db: Session, attempt_id: int) -> set[int]:
    classic = {
        row.step_id
        for row in db.query(AttemptResponse.step_id).outerjoin(
            AudioSubmission,
            AudioSubmission.response_id == AttemptResponse.id,
        ).filter(
            AttemptResponse.attempt_id == attempt_id,
            or_(AudioSubmission.id.is_(None), AudioSubmission.status != "rerecord_required"),
        ).all()
    }
    structured = {
        row.step_id
        for row in db.query(ActivityStepResponse.step_id).filter(
            ActivityStepResponse.attempt_id == attempt_id,
        ).all()
    }
    return classic | structured


def _completed_response_count(db: Session, attempt_id: int) -> int:
    classic = db.query(AttemptResponse.id).filter(AttemptResponse.attempt_id == attempt_id).count()
    structured = db.query(ActivityStepResponse.id).filter(
        ActivityStepResponse.attempt_id == attempt_id,
    ).count()
    return classic + structured


def _criterion_parts(item: ContentItem) -> list[str]:
    criterion = str((item.template_data or {}).get("criterion") or "").strip()
    if not criterion or criterion in {"بالترتيب المذكور", "مطابقة", "الدقة والاسترسال"}:
        return []
    return [part.strip(" .") for part in re.split(r"\s+ثم\s+|[،,]", criterion) if part.strip(" .")]


def _expected_order_ids(item: ContentItem, step: ContentStep) -> list[int]:
    ordered = sorted(step.options, key=lambda option: option.order_index)
    parts = _criterion_parts(item)
    if not parts:
        return [option.id for option in ordered]

    unused = list(ordered)
    result: list[int] = []
    for part in parts:
        key = semantic_key(part)
        match = next(
            (
                option
                for option in unused
                if semantic_key(option.text) == key
                or key in semantic_key(option.text)
                or semantic_key(option.text) in key
            ),
            None,
        )
        if not match:
            return [option.id for option in ordered]
        result.append(match.id)
        unused.remove(match)
    return result


def _validate_option_ids(step: ContentStep, selected_ids: list[int]) -> None:
    allowed = {option.id for option in step.options}
    if not selected_ids or any(option_id not in allowed for option_id in selected_ids):
        raise HTTPException(status_code=400, detail="الإجابة المختارة لا تنتمي إلى هذا السؤال")
    if len(set(selected_ids)) != len(selected_ids):
        raise HTTPException(status_code=400, detail="لا يمكن اختيار العنصر نفسه أكثر من مرة")


@router.post("/start", response_model=schemas.AssessmentSessionResponse)
def start_assessment(
    request: schemas.AssessmentStartRequest,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    if not student.is_active:
        raise HTTPException(status_code=403, detail="حساب الطالب غير نشط")

    active = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.status == "in_progress",
    ).first()
    if active:
        if active.session_type == request.session_type:
            return active
        raise HTTPException(status_code=409, detail="أكمل الجلسة الحالية أولًا")

    completed = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.session_type == request.session_type,
        AssessmentSession.status == "completed",
    ).first()
    if completed:
        raise HTTPException(status_code=409, detail="هذا الاختبار مكتمل بالفعل")

    if request.session_type == "posttest":
        pretest_completed = db.query(AssessmentSession.id).filter(
            AssessmentSession.student_id == student.id,
            AssessmentSession.session_type == "pretest",
            AssessmentSession.status == "completed",
        ).first()
        if not pretest_completed:
            raise HTTPException(status_code=409, detail="أكمل الاختبار القبلي أولًا")
        if not student.posttest_enabled:
            raise HTTPException(status_code=403, detail="لم يفتح المشرف الاختبار البعدي بعد")

    new_session = AssessmentSession(
        student_id=student.id,
        session_type=request.session_type,
        status="in_progress",
    )
    db.add(new_session)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        active = db.query(AssessmentSession).filter(
            AssessmentSession.student_id == student.id,
            AssessmentSession.status == "in_progress",
        ).first()
        if active and active.session_type == request.session_type:
            return active
        raise HTTPException(status_code=409, detail="تعذر بدء الاختبار بسبب تعارض في الجلسة")
    db.refresh(new_session)
    return new_session


@router.get("/active", response_model=Optional[schemas.AssessmentSessionResponse])
def get_active_session(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.status == "in_progress",
    ).first()


@router.get("/session/{session_id}/next", response_model=Optional[schemas.ContentItemResponse])
def get_next_item(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = _session_for_student(db, session_id, student.id, require_active=False)
    if session.status == "completed":
        return None

    pending_attempt = db.query(Attempt).filter(
        Attempt.session_id == session_id,
        Attempt.status == "in_progress",
    ).order_by(Attempt.id).first()
    if pending_attempt:
        item = _load_item(db, pending_attempt.item_id)
        if not item:
            raise HTTPException(status_code=409, detail="تعذر تحميل محتوى السؤال")
        answered_step_ids = _answered_step_ids(db, pending_attempt.id)
        next_step = next((step for step in item.steps if step.id not in answered_step_ids), None)
        if next_step:
            return _item_step_payload(item, next_step)
        pending_attempt.status = "completed"
        pending_attempt.completed_at = datetime.now(timezone.utc)
        db.commit()

    attempted_item_ids = [
        row.item_id
        for row in db.query(Attempt.item_id).filter(
            Attempt.session_id == session_id,
            Attempt.status == "completed",
        ).all()
    ]
    query = db.query(ContentItem).filter(
        ContentItem.kind == KIND_BY_SESSION_TYPE[session.session_type],
    )
    if attempted_item_ids:
        query = query.filter(ContentItem.id.notin_(attempted_item_ids))
    next_item = query.order_by(ContentItem.order_index).first()
    if not next_item:
        return None

    attempt = Attempt(session_id=session_id, item_id=next_item.id, status="in_progress")
    db.add(attempt)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        attempt = db.query(Attempt).filter(
            Attempt.session_id == session_id,
            Attempt.item_id == next_item.id,
        ).one()

    item = _load_item(db, next_item.id)
    first_step = next(iter(item.steps if item else []), None)
    if not item or not first_step:
        raise HTTPException(status_code=409, detail="السؤال لا يحتوي على مهمة قابلة للتنفيذ")
    return _item_step_payload(item, first_step)


@router.get("/session/{session_id}/progress", response_model=schemas.AssessmentProgressResponse)
def get_session_progress(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = _session_for_student(db, session_id, student.id)
    completed_items = db.query(Attempt).filter(
        Attempt.session_id == session_id,
        Attempt.status == "completed",
    ).count()
    has_pending_item = db.query(Attempt.id).filter(
        Attempt.session_id == session_id,
        Attempt.status == "in_progress",
    ).first() is not None
    total_items = db.query(ContentItem).filter(
        ContentItem.kind == KIND_BY_SESSION_TYPE[session.session_type],
    ).count()
    classic_steps = db.query(AttemptResponse.id).join(
        Attempt, Attempt.id == AttemptResponse.attempt_id,
    ).filter(Attempt.session_id == session_id).count()
    structured_steps = db.query(ActivityStepResponse.id).join(
        Attempt, Attempt.id == ActivityStepResponse.attempt_id,
    ).filter(Attempt.session_id == session_id).count()
    total_steps = db.query(func.count(ContentStep.id)).join(
        ContentItem, ContentItem.id == ContentStep.item_id,
    ).filter(ContentItem.kind == KIND_BY_SESSION_TYPE[session.session_type]).scalar() or 0
    return {
        "completed_items": completed_items,
        "total_items": total_items,
        "completed_steps": classic_steps + structured_steps,
        "total_steps": total_steps,
        "has_pending_item": has_pending_item,
        "elapsed_seconds": session.elapsed_seconds,
    }


@router.post("/session/{session_id}/attempt/{item_id}/submit")
def submit_attempt(
    session_id: int,
    item_id: int,
    submission: AssessmentAnswerRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    idempotency_key = _validate_idempotency_key(idempotency_key)
    operation = f"assessment.answer:{session_id}:{item_id}"
    request_hash = _request_hash(submission.model_dump(mode="json"))
    replay = _idempotency_replay(db, student.id, operation, idempotency_key, request_hash)
    if replay is not None:
        return replay

    session = _session_for_student(db, session_id, student.id)
    attempt = db.query(Attempt).filter(
        Attempt.session_id == session_id,
        Attempt.item_id == item_id,
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="لم يتم العثور على محاولة هذا السؤال")

    item = _load_item(db, item_id)
    step = next((candidate for candidate in (item.steps if item else []) if candidate.id == submission.step_id), None)
    if not item or not step:
        raise HTTPException(status_code=400, detail="السؤال أو الخطوة غير صالحين")

    interaction = canonical_interaction(item)
    existing_response = db.query(AttemptResponse).filter(
        AttemptResponse.attempt_id == attempt.id,
        AttemptResponse.step_id == submission.step_id,
    ).first()
    existing_structured = _structured_response_exists(db, attempt.id, submission.step_id)
    is_correct: bool | None = None

    if interaction in AUDIO_INTERACTIONS:
        if submission.selected_option_id is not None or submission.selected_option_ids or not submission.audio_storage_key:
            raise HTTPException(status_code=400, detail="سجّل قراءتك ثم أرسل التسجيل")
        expected_prefix = f"audio/{student.id}/"
        if not submission.audio_storage_key.startswith(expected_prefix):
            raise HTTPException(status_code=403, detail="ملف التسجيل لا يخص هذا الطالب")
        if submission.audio_file_size is None:
            raise HTTPException(status_code=400, detail="بيانات التسجيل غير مكتملة")
        if not (submission.audio_mime_type or "").startswith("audio/"):
            raise HTTPException(status_code=400, detail="صيغة التسجيل الصوتي غير مدعومة")
        try:
            storage.verify_audio(
                submission.audio_storage_key,
                submission.audio_file_size,
                submission.audio_mime_type,
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="تعذر التحقق من ملف التسجيل")
        except RuntimeError:
            raise HTTPException(status_code=503, detail="خدمة حفظ التسجيلات غير متاحة الآن")

        if existing_response:
            audio = db.query(AudioSubmission).filter(AudioSubmission.response_id == existing_response.id).first()
            if not audio or audio.status != "rerecord_required":
                raise HTTPException(status_code=409, detail="تم إرسال هذه القراءة مسبقًا")
            audio.storage_key = submission.audio_storage_key
            audio.file_size = submission.audio_file_size
            audio.mime_type = submission.audio_mime_type
            audio.duration_seconds = submission.audio_duration_seconds
            audio.status = "uploaded"
            audio.submitted_at = datetime.now(timezone.utc)
            existing_response.is_correct = None
            existing_response.submitted_at = datetime.now(timezone.utc)
            existing_response.elapsed_seconds += submission.elapsed_seconds
        else:
            response = AttemptResponse(
                attempt_id=attempt.id,
                step_id=step.id,
                selected_option_id=None,
                is_correct=None,
                elapsed_seconds=submission.elapsed_seconds,
            )
            db.add(response)
            db.flush()
            db.add(AudioSubmission(
                response_id=response.id,
                storage_key=submission.audio_storage_key,
                file_size=submission.audio_file_size,
                mime_type=submission.audio_mime_type or "audio/webm",
                duration_seconds=submission.audio_duration_seconds,
            ))

    elif interaction in SINGLE_INTERACTIONS:
        if existing_response or existing_structured:
            raise HTTPException(status_code=409, detail="تم إرسال إجابة هذا السؤال مسبقًا")
        if submission.audio_storage_key or submission.selected_option_id is None:
            raise HTTPException(status_code=400, detail="اختر إجابة قبل المتابعة")
        option = next((candidate for candidate in step.options if candidate.id == submission.selected_option_id), None)
        if not option:
            raise HTTPException(status_code=400, detail="الإجابة المختارة غير صالحة")
        is_correct = bool(option.is_correct)
        db.add(AttemptResponse(
            attempt_id=attempt.id,
            step_id=step.id,
            selected_option_id=option.id,
            is_correct=is_correct,
            elapsed_seconds=submission.elapsed_seconds,
        ))

    elif interaction in STRUCTURED_INTERACTIONS:
        if existing_response or existing_structured:
            raise HTTPException(status_code=409, detail="تم إرسال إجابة هذا السؤال مسبقًا")
        selected_ids = submission.selected_option_ids
        _validate_option_ids(step, selected_ids)
        if interaction in {"sequence", "memory_sequence", "path_sequence", "build_word"}:
            expected_ids = _expected_order_ids(item, step)
            is_correct = selected_ids == expected_ids
        else:
            expected_ids = [option.id for option in step.options if option.is_correct]
            is_correct = set(selected_ids) == set(expected_ids)
        db.add(ActivityStepResponse(
            attempt_id=attempt.id,
            step_id=step.id,
            attempt_no=1,
            response_payload={"selected_option_ids": selected_ids},
            is_correct=bool(is_correct),
            hint_used=False,
            elapsed_seconds=submission.elapsed_seconds,
        ))
    else:
        raise HTTPException(status_code=409, detail="نوع هذا السؤال غير مدعوم حاليًا")

    db.flush()
    total_steps = len(item.steps)
    if _completed_response_count(db, attempt.id) >= total_steps:
        attempt.status = "completed"
        attempt.completed_at = datetime.now(timezone.utc)
    attempt.elapsed_seconds += submission.elapsed_seconds
    session.elapsed_seconds += submission.elapsed_seconds
    session.updated_at = datetime.now(timezone.utc)

    response_json = {"status": "ok", "is_correct": is_correct}
    _store_idempotency(db, student.id, operation, idempotency_key, request_hash, response_json)
    return _commit_idempotent(db, student.id, operation, idempotency_key, request_hash, response_json)


@router.post("/session/{session_id}/finish", response_model=schemas.SessionFinishResponse)
def finish_session(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.student_id == student.id,
    ).first()
    if not session:
        raise HTTPException(status_code=400, detail="الجلسة غير صالحة أو مكتملة")
    if session.status == "completed":
        if session.final_score is None or session.assigned_level is None:
            raise HTTPException(status_code=409, detail="نتيجة الجلسة المكتملة غير متاحة")
        return {
            "id": session.id,
            "final_score": session.final_score,
            "assigned_level": session.assigned_level,
        }
    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="الجلسة غير صالحة أو مكتملة")

    rerecord_exists = db.query(AudioSubmission).join(
        AttemptResponse, AttemptResponse.id == AudioSubmission.response_id,
    ).join(Attempt, Attempt.id == AttemptResponse.attempt_id).filter(
        Attempt.session_id == session_id,
        AudioSubmission.status == "rerecord_required",
    ).first()
    if rerecord_exists:
        raise HTTPException(status_code=409, detail="يوجد تسجيل يحتاج إلى إعادة قبل إنهاء الاختبار")

    if session.session_type in ["pretest", "posttest"]:
        required_items = db.query(ContentItem).filter(
            ContentItem.kind == KIND_BY_SESSION_TYPE[session.session_type],
        ).count()
        attempts = db.query(Attempt).filter(Attempt.session_id == session_id).all()
        if required_items != 30 or len(attempts) != required_items or any(attempt.status != "completed" for attempt in attempts):
            raise HTTPException(status_code=400, detail="أكمل الأسئلة الثلاثين قبل إنهاء الاختبار")

    total_score = Decimal("0.0")
    attempts = db.query(Attempt).filter(Attempt.session_id == session_id).all()
    for attempt in attempts:
        responses = db.query(AttemptResponse).filter(AttemptResponse.attempt_id == attempt.id).all()
        for response in responses:
            audio_sub = db.query(AudioSubmission).filter(AudioSubmission.response_id == response.id).first()
            if audio_sub:
                if audio_sub.status == "uploaded":
                    raise HTTPException(status_code=409, detail="يوجد تسجيل صوتي في انتظار المراجعة")
                if audio_sub.status == "graded":
                    review = db.query(AudioReview).filter(
                        AudioReview.submission_id == audio_sub.id,
                    ).order_by(AudioReview.id.desc()).first()
                    if review:
                        total_score += review.rubric_score
            elif response.is_correct:
                total_score += Decimal("1.0")
        structured = db.query(ActivityStepResponse).filter(
            ActivityStepResponse.attempt_id == attempt.id,
        ).all()
        total_score += sum((Decimal("1.0") for response in structured if response.is_correct), Decimal("0.0"))

    final_percentage = (total_score / Decimal("30.0")) * Decimal("100.0")
    if final_percentage < Decimal("50.0"):
        assigned_level = 1
    elif final_percentage < Decimal("80.0"):
        assigned_level = 2
    else:
        assigned_level = 3

    session.final_score = final_percentage
    session.assigned_level = assigned_level
    session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)
    session.updated_at = datetime.now(timezone.utc)
    if session.session_type in ["pretest", "posttest"]:
        student.current_level = assigned_level
    if session.session_type == "posttest":
        student.posttest_enabled = False
        student.posttest_enabled_at = None
        student.posttest_enabled_by = None
    db.commit()
    return {"id": session.id, "final_score": final_percentage, "assigned_level": assigned_level}


@router.post("/session/{session_id}/upload-audio")
def upload_audio_submission(
    session_id: int,
    file: UploadFile = File(...),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    idempotency_key = _validate_idempotency_key(idempotency_key)
    _session_for_student(db, session_id, student.id)
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="اختر ملفًا صوتيًا صالحًا")

    operation = f"assessment.audio.upload:{session_id}"
    try:
        storage_key, file_size, digest = storage.upload_audio(file, student.id, f"{session_id}:{idempotency_key}")
        request_hash = _request_hash({
            "sha256": digest,
            "content_type": file.content_type,
            "file_size": file_size,
        })
        replay = _idempotency_replay(db, student.id, operation, idempotency_key, request_hash)
        if replay is not None:
            return replay
        response_json = {
            "audio_storage_key": storage_key,
            "audio_file_size": file_size,
            "audio_mime_type": file.content_type,
        }
        _store_idempotency(db, student.id, operation, idempotency_key, request_hash, response_json)
        return _commit_idempotent(db, student.id, operation, idempotency_key, request_hash, response_json)
    except ValueError:
        raise HTTPException(status_code=400, detail="ملف التسجيل غير صالح")
    except RuntimeError:
        raise HTTPException(status_code=503, detail="خدمة حفظ التسجيلات غير متاحة الآن")
