"""structured learning activity runtime

Revision ID: 0005_activity_runtime
Revises: 0004_student_lifecycle
Create Date: 2026-08-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0005_activity_runtime"
down_revision = "0004_student_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "activity_step_responses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("step_id", sa.Integer(), nullable=False),
        sa.Column("attempt_no", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "response_payload",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("hint_used", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("elapsed_seconds", sa.Integer(), server_default="0", nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["attempt_id"], ["attempts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["step_id"], ["content_steps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "attempt_id",
            "step_id",
            "attempt_no",
            name="uq_activity_step_response_attempt_step_no",
        ),
    )
    op.create_index(
        op.f("ix_activity_step_responses_id"),
        "activity_step_responses",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_activity_step_responses_id"), table_name="activity_step_responses")
    op.drop_table("activity_step_responses")
