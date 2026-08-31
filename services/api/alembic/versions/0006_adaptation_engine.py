"""adaptive learning decisions and rewards

Revision ID: 0006_adaptation_engine
Revises: 0005_activity_runtime
Create Date: 2026-08-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0006_adaptation_engine"
down_revision = "0005_activity_runtime"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "adaptation_decisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("decision_source", sa.String(length=20), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("mastery_score", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("previous_level", sa.Integer(), nullable=False),
        sa.Column("new_level", sa.Integer(), nullable=False),
        sa.Column("weakest_skill_id", sa.Integer(), nullable=True),
        sa.Column("recommended_item_id", sa.Integer(), nullable=True),
        sa.Column("valid_attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("consecutive_low_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("snapshot_key", sa.String(length=200), nullable=True),
        sa.Column(
            "explanation",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("manual_reason", sa.String(), nullable=True),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["recommended_item_id"], ["content_items.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["weakest_skill_id"], ["skills.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "student_id",
            "decision_source",
            "snapshot_key",
            name="uq_adaptation_decision_student_source_snapshot",
        ),
    )
    op.create_index(op.f("ix_adaptation_decisions_id"), "adaptation_decisions", ["id"], unique=False)
    op.create_index(op.f("ix_adaptation_decisions_student_id"), "adaptation_decisions", ["student_id"], unique=False)

    op.create_table(
        "reward_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=True),
        sa.Column("reward_type", sa.String(length=20), nullable=False),
        sa.Column("reward_key", sa.String(length=120), nullable=False),
        sa.Column("stars", sa.Integer(), nullable=True),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column(
            "details",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["attempt_id"], ["attempts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "reward_key", name="uq_reward_event_student_key"),
    )
    op.create_index(op.f("ix_reward_events_id"), "reward_events", ["id"], unique=False)
    op.create_index(op.f("ix_reward_events_student_id"), "reward_events", ["student_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reward_events_student_id"), table_name="reward_events")
    op.drop_index(op.f("ix_reward_events_id"), table_name="reward_events")
    op.drop_table("reward_events")
    op.drop_index(op.f("ix_adaptation_decisions_student_id"), table_name="adaptation_decisions")
    op.drop_index(op.f("ix_adaptation_decisions_id"), table_name="adaptation_decisions")
    op.drop_table("adaptation_decisions")
