"""Durable asynchronous speech-analysis pipeline for P07."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import os

from sqlalchemy.orm import Session

from db.models import AudioSubmission, AttemptResponse, ContentStep
from db.speech_models import SpeechAnalysis, SpeechAnalysisJob
from speech_alignment import align_reference, alignment_counts
from speech_provider import (
    ProviderNotConfigured,
    ProviderPermanentError,
    ProviderTemporaryError,
    SpeechProvider,
    build_provider,
)
import storage


RETRY_SECONDS = (30, 120, 600)


def enqueue_submission(db: Session, submission_id: int) -> SpeechAnalysisJob:
    """Idempotently create one queue job per stored audio submission."""
    submission = db.query(AudioSubmission).filter(AudioSubmission.id == submission_id).first()
    if not submission:
        raise ValueError("Audio submission not found")

    existing = db.query(SpeechAnalysisJob).filter(
        SpeechAnalysisJob.submission_id == submission_id
    ).first()
    if existing:
        return existing

    job = SpeechAnalysisJob(submission_id=submission_id, status="queued")
    db.add(job)
    db.flush()
    return job


def _reference_for_submission(db: Session, submission: AudioSubmission) -> str:
    step = db.query(ContentStep).join(
        AttemptResponse, AttemptResponse.step_id == ContentStep.id
    ).filter(AttemptResponse.id == submission.response_id).first()
    if not step:
        raise ProviderPermanentError("Audio submission has no content step")
    reference = (step.expected_reading_text or step.prompt_text or "").strip()
    if not reference:
        raise ProviderPermanentError("Audio content has no reference reading text")
    return reference


def _audio_bytes(submission: AudioSubmission) -> bytes:
    try:
        response = storage.s3_client.get_object(
            Bucket=storage.S3_BUCKET_NAME,
            Key=submission.storage_key,
        )
        payload = response["Body"].read(storage.MAX_AUDIO_BYTES + 1)
    except Exception as exc:  # boto errors are retryable infrastructure failures
        raise ProviderTemporaryError("Private audio storage is unavailable") from exc
    if not payload or len(payload) > storage.MAX_AUDIO_BYTES:
        raise ProviderPermanentError("Stored audio is empty or outside the allowed size")
    return payload


def _calibrated_decision(confidence: float | None) -> tuple[str, str | None]:
    """Return a conservative machine decision.

    The project source requires the confidence threshold to be calibrated on
    representative samples. Until both a threshold and calibration version are
    explicitly configured, every valid ASR result remains review_required.
    """
    raw_threshold = os.getenv("HIMMA_ASR_CONFIDENCE_THRESHOLD", "").strip()
    calibration_version = os.getenv("HIMMA_ASR_CALIBRATION_VERSION", "").strip() or None
    if not raw_threshold or not calibration_version or confidence is None:
        return "review_required", calibration_version
    try:
        threshold = float(raw_threshold)
    except ValueError:
        return "review_required", calibration_version
    if not 0.0 <= threshold <= 1.0:
        return "review_required", calibration_version
    return ("auto_accepted" if confidence >= threshold else "review_required"), calibration_version


def _token_payload(aligned, provider_words):
    words = list(provider_words or ())
    payload = []
    for token in aligned:
        word = None
        if token.hypothesis_index is not None and token.hypothesis_index < len(words):
            word = words[token.hypothesis_index]
        payload.append({
            "kind": token.kind,
            "reference": token.reference,
            "hypothesis": token.hypothesis,
            "reference_index": token.reference_index,
            "hypothesis_index": token.hypothesis_index,
            "start_seconds": getattr(word, "start_seconds", None),
            "end_seconds": getattr(word, "end_seconds", None),
            "confidence": getattr(word, "confidence", None),
        })
    return payload


def process_job(
    db: Session,
    job_id: int,
    *,
    provider: SpeechProvider | None = None,
    now: datetime | None = None,
) -> SpeechAnalysisJob:
    """Process exactly one job; safe to call repeatedly.

    Runtime provider absence is an explicit blocked state, not a fake result.
    Temporary failures back off and eventually dead-letter. Permanent failures
    fail closed. No student score is mutated here.
    """
    now = now or datetime.now(timezone.utc)
    job = db.query(SpeechAnalysisJob).filter(SpeechAnalysisJob.id == job_id).first()
    if not job:
        raise ValueError("Speech analysis job not found")
    if job.status in {"completed", "review_required", "failed", "dead_letter"}:
        return job
    if job.status == "retry_wait" and job.next_attempt_at and job.next_attempt_at > now:
        return job

    existing = db.query(SpeechAnalysis).filter(SpeechAnalysis.job_id == job.id).first()
    if existing:
        job.status = "completed" if existing.decision == "auto_accepted" else "review_required"
        job.completed_at = job.completed_at or now
        job.updated_at = now
        db.flush()
        return job

    submission = db.query(AudioSubmission).filter(AudioSubmission.id == job.submission_id).first()
    if not submission:
        job.status = "failed"
        job.last_error_code = "submission_missing"
        job.last_error_message = "Audio submission not found"
        job.updated_at = now
        db.flush()
        return job

    job.status = "processing"
    job.updated_at = now
    db.flush()

    try:
        reference = _reference_for_submission(db, submission)
        payload = _audio_bytes(submission)
        runtime_provider = provider or build_provider()
        result = runtime_provider.transcribe_reference_guided(
            audio_bytes=payload,
            mime_type=submission.mime_type,
            reference_text=reference,
            language="ar",
        )
        aligned = align_reference(reference, result.transcript)
        counts = alignment_counts(aligned)
        decision, calibration_version = _calibrated_decision(result.confidence)
        analysis = SpeechAnalysis(
            job_id=job.id,
            submission_id=submission.id,
            provider_name=result.provider_name,
            provider_model=result.model,
            provider_request_id=result.request_id,
            reference_text=reference,
            transcript_text=result.transcript,
            overall_confidence=(Decimal(str(result.confidence)) if result.confidence is not None else None),
            decision=decision,
            correct_count=counts["correct"],
            deletion_count=counts["deletion"],
            insertion_count=counts["insertion"],
            substitution_count=counts["substitution"],
            duration_seconds=(Decimal(str(result.duration_seconds)) if result.duration_seconds is not None else None),
            tokens_json=_token_payload(aligned, result.words),
            provider_payload=result.raw_metadata or None,
            calibration_version=calibration_version,
        )
        db.add(analysis)
        job.attempt_count += 1
        job.status = "completed" if decision == "auto_accepted" else "review_required"
        job.last_error_code = None
        job.last_error_message = None
        job.next_attempt_at = None
        job.completed_at = now
        job.updated_at = now
        db.flush()
        return job
    except ProviderNotConfigured as exc:
        job.status = "blocked_provider"
        job.last_error_code = "provider_not_configured"
        job.last_error_message = str(exc)
        job.next_attempt_at = None
        job.updated_at = now
        db.flush()
        return job
    except ProviderTemporaryError as exc:
        job.attempt_count += 1
        job.last_error_code = "temporary_provider_error"
        job.last_error_message = str(exc)
        if job.attempt_count >= job.max_attempts:
            job.status = "dead_letter"
            job.next_attempt_at = None
        else:
            delay = RETRY_SECONDS[min(job.attempt_count - 1, len(RETRY_SECONDS) - 1)]
            job.status = "retry_wait"
            job.next_attempt_at = now + timedelta(seconds=delay)
        job.updated_at = now
        db.flush()
        return job
    except ProviderPermanentError as exc:
        job.attempt_count += 1
        job.status = "failed"
        job.last_error_code = "permanent_analysis_error"
        job.last_error_message = str(exc)
        job.next_attempt_at = None
        job.updated_at = now
        db.flush()
        return job


def claimable_job_ids(db: Session, *, now: datetime | None = None, limit: int = 10) -> list[int]:
    now = now or datetime.now(timezone.utc)
    rows = db.query(SpeechAnalysisJob.id).filter(
        (SpeechAnalysisJob.status == "queued")
        | ((SpeechAnalysisJob.status == "retry_wait") & (SpeechAnalysisJob.next_attempt_at <= now))
    ).order_by(SpeechAnalysisJob.created_at, SpeechAnalysisJob.id).limit(limit).all()
    return [row.id for row in rows]
