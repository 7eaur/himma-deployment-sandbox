"""durable reinforcement verification cycles

Revision ID: 0008_reinforcement_cycles
Revises: 0007_speech_analysis_pipeline
Create Date: 2026-08-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0008_reinforcement_cycles"
down_revision = "0007_speech_analysis_pipeline"
branch_labels = None
depends_on = None


def _json_type():
    return sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.create_table(
        "reinforcement_cycles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("decision_id", sa.Integer(), nullable=False),
        sa.Column("source_attempt_id", sa.Integer(), nullable=False),
        sa.Column("source_step_ids", _json_type(), nullable=False),
        sa.Column("reinforcement_item_id", sa.Integer(), nullable=False),
        sa.Column("reinforcement_attempt_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="reinforcement_pending", nullable=False),
        sa.Column("verification_round", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_verification_rounds", sa.Integer(), server_default="2", nullable=False),
        sa.Column("escalation_reason", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('reinforcement_pending','reinforcement_in_progress','verification_pending','verified','escalated')",
            name="ck_reinforcement_cycles_status",
        ),
        sa.CheckConstraint("verification_round >= 0", name="ck_reinforcement_cycles_verification_round"),
        sa.CheckConstraint(
            "max_verification_rounds BETWEEN 1 AND 5",
            name="ck_reinforcement_cycles_max_verification_rounds",
        ),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["assessment_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["decision_id"], ["adaptation_decisions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_attempt_id"], ["attempts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reinforcement_item_id"], ["content_items.id"]),
        sa.ForeignKeyConstraint(["reinforcement_attempt_id"], ["attempts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("decision_id", name="uq_reinforcement_cycle_decision"),
    )
    op.create_index("ix_reinforcement_cycles_id", "reinforcement_cycles", ["id"], unique=False)
    op.create_index("ix_reinforcement_cycles_student_id", "reinforcement_cycles", ["student_id"], unique=False)
    op.create_index("ix_reinforcement_cycles_session_id", "reinforcement_cycles", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_reinforcement_cycles_session_id", table_name="reinforcement_cycles")
    op.drop_index("ix_reinforcement_cycles_student_id", table_name="reinforcement_cycles")
    op.drop_index("ix_reinforcement_cycles_id", table_name="reinforcement_cycles")
    op.drop_table("reinforcement_cycles")
