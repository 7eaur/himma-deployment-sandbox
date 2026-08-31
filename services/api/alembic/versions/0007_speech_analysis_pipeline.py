"""speech analysis queue and results

Revision ID: 0007_speech_analysis_pipeline
Revises: 0006_adaptation_engine
Create Date: 2026-08-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0007_speech_analysis_pipeline"
down_revision = "0006_adaptation_engine"
branch_labels = None
depends_on = None


def _json_type():
    return sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.create_table(
        "speech_analysis_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("submission_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="queued", nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default="3", nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(length=100), nullable=True),
        sa.Column("last_error_message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("attempt_count >= 0", name="ck_speech_jobs_attempt_count"),
        sa.CheckConstraint("max_attempts BETWEEN 1 AND 10", name="ck_speech_jobs_max_attempts"),
        sa.CheckConstraint(
            "status IN ('queued','processing','retry_wait','completed','review_required','failed','dead_letter','blocked_provider')",
            name="ck_speech_jobs_status",
        ),
        sa.ForeignKeyConstraint(["submission_id"], ["audio_submissions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("submission_id", name="uq_speech_analysis_jobs_submission"),
    )
    op.create_index("ix_speech_analysis_jobs_id", "speech_analysis_jobs", ["id"], unique=False)
    op.create_index("ix_speech_jobs_claim", "speech_analysis_jobs", ["status", "next_attempt_at", "created_at"], unique=False)

    op.create_table(
        "speech_analyses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("submission_id", sa.Integer(), nullable=False),
        sa.Column("provider_name", sa.String(length=100), nullable=False),
        sa.Column("provider_model", sa.String(length=150), nullable=True),
        sa.Column("provider_request_id", sa.String(length=200), nullable=True),
        sa.Column("reference_text", sa.String(), nullable=False),
        sa.Column("transcript_text", sa.String(), nullable=False),
        sa.Column("overall_confidence", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("correct_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("deletion_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("insertion_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("substitution_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("duration_seconds", sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column("tokens_json", _json_type(), nullable=False),
        sa.Column("provider_payload", _json_type(), nullable=True),
        sa.Column("calibration_version", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "decision IN ('auto_accepted','review_required','rerecord_required')",
            name="ck_speech_analyses_decision",
        ),
        sa.CheckConstraint(
            "overall_confidence IS NULL OR (overall_confidence >= 0 AND overall_confidence <= 1)",
            name="ck_speech_analyses_confidence",
        ),
        sa.ForeignKeyConstraint(["job_id"], ["speech_analysis_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["submission_id"], ["audio_submissions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", name="uq_speech_analyses_job"),
        sa.UniqueConstraint("submission_id", name="uq_speech_analyses_submission"),
    )
    op.create_index("ix_speech_analyses_id", "speech_analyses", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_speech_analyses_id", table_name="speech_analyses")
    op.drop_table("speech_analyses")
    op.drop_index("ix_speech_jobs_claim", table_name="speech_analysis_jobs")
    op.drop_index("ix_speech_analysis_jobs_id", table_name="speech_analysis_jobs")
    op.drop_table("speech_analysis_jobs")
