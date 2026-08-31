from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB

from db.models import Base


class SpeechAnalysisJob(Base):
    """Durable DB-backed queue entry for asynchronous speech analysis.

    P07 intentionally keeps provider execution outside the request path. Jobs are
    retried deterministically and may end in dead_letter rather than silently
    awarding or penalising a student when the provider is unavailable.
    """

    __tablename__ = "speech_analysis_jobs"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("audio_submissions.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(32), nullable=False, default="queued", server_default="queued")
    attempt_count = Column(Integer, nullable=False, default=0, server_default="0")
    max_attempts = Column(Integer, nullable=False, default=3, server_default="3")
    next_attempt_at = Column(DateTime(timezone=True), nullable=True)
    last_error_code = Column(String(100), nullable=True)
    last_error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("submission_id", name="uq_speech_analysis_jobs_submission"),
        CheckConstraint("attempt_count >= 0", name="ck_speech_jobs_attempt_count"),
        CheckConstraint("max_attempts BETWEEN 1 AND 10", name="ck_speech_jobs_max_attempts"),
        CheckConstraint(
            "status IN ('queued','processing','retry_wait','completed','review_required','failed','dead_letter','blocked_provider')",
            name="ck_speech_jobs_status",
        ),
        Index("ix_speech_jobs_claim", "status", "next_attempt_at", "created_at"),
    )


class SpeechAnalysis(Base):
    """Immutable machine-analysis result for one audio submission."""

    __tablename__ = "speech_analyses"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("speech_analysis_jobs.id", ondelete="CASCADE"), nullable=False)
    submission_id = Column(Integer, ForeignKey("audio_submissions.id", ondelete="CASCADE"), nullable=False)
    provider_name = Column(String(100), nullable=False)
    provider_model = Column(String(150), nullable=True)
    provider_request_id = Column(String(200), nullable=True)
    reference_text = Column(String, nullable=False)
    transcript_text = Column(String, nullable=False)
    overall_confidence = Column(Numeric(precision=10, scale=6), nullable=True)
    decision = Column(String(32), nullable=False)
    correct_count = Column(Integer, nullable=False, default=0, server_default="0")
    deletion_count = Column(Integer, nullable=False, default=0, server_default="0")
    insertion_count = Column(Integer, nullable=False, default=0, server_default="0")
    substitution_count = Column(Integer, nullable=False, default=0, server_default="0")
    duration_seconds = Column(Numeric(precision=10, scale=3), nullable=True)
    tokens_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    provider_payload = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    calibration_version = Column(String(80), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("job_id", name="uq_speech_analyses_job"),
        UniqueConstraint("submission_id", name="uq_speech_analyses_submission"),
        CheckConstraint(
            "decision IN ('auto_accepted','review_required','rerecord_required')",
            name="ck_speech_analyses_decision",
        ),
        CheckConstraint(
            "overall_confidence IS NULL OR (overall_confidence >= 0 AND overall_confidence <= 1)",
            name="ck_speech_analyses_confidence",
        ),
    )
