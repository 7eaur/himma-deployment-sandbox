"""durable assessment retake lifecycle

Revision ID: 0009_assessment_retakes
Revises: 0008_reinforcement_cycles
Create Date: 2026-08-31
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_assessment_retakes"
down_revision = "0008_reinforcement_cycles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The old schema allowed only one pre/post session per student. Retakes must
    # preserve history, so uniqueness moves to attempt numbering instead. Core
    # sessions are deliberately excluded because L1/L2/L3 each own a durable
    # Core session and all use the neutral default attempt number 1.
    op.drop_index("uq_assessment_sessions_prepost_once", table_name="assessment_sessions")

    op.add_column(
        "assessment_sessions",
        sa.Column("assessment_attempt_no", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column(
        "assessment_sessions",
        sa.Column("supersedes_session_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "assessment_sessions",
        sa.Column("official_for_reporting", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_foreign_key(
        "fk_assessment_sessions_supersedes_session",
        "assessment_sessions",
        "assessment_sessions",
        ["supersedes_session_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "uq_assessment_sessions_prepost_attempt_no",
        "assessment_sessions",
        ["student_id", "session_type", "assessment_attempt_no"],
        unique=True,
        postgresql_where=sa.text("session_type IN ('pretest', 'posttest')"),
        sqlite_where=sa.text("session_type IN ('pretest', 'posttest')"),
    )
    op.create_check_constraint(
        "ck_assessment_sessions_attempt_no",
        "assessment_sessions",
        "assessment_attempt_no >= 1",
    )

    # Existing completed pre/post sessions are the official baseline attempts.
    op.execute(
        """
        UPDATE assessment_sessions
        SET official_for_reporting = TRUE
        WHERE session_type IN ('pretest', 'posttest') AND status = 'completed'
        """
    )

    op.create_table(
        "assessment_retake_authorizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("session_type", sa.String(length=50), nullable=False),
        sa.Column("previous_session_id", sa.Integer(), nullable=False),
        sa.Column("authorized_by", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("new_session_id", sa.Integer(), nullable=True),
        sa.CheckConstraint("session_type IN ('pretest','posttest')", name="ck_assessment_retake_type"),
        sa.CheckConstraint("status IN ('pending','consumed','revoked')", name="ck_assessment_retake_status"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["previous_session_id"], ["assessment_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["authorized_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["new_session_id"], ["assessment_sessions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_assessment_retake_authorizations_id",
        "assessment_retake_authorizations",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_assessment_retake_authorizations_student_id",
        "assessment_retake_authorizations",
        ["student_id"],
        unique=False,
    )
    op.create_index(
        "uq_assessment_retake_pending",
        "assessment_retake_authorizations",
        ["student_id", "session_type"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
        sqlite_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    op.drop_index("uq_assessment_retake_pending", table_name="assessment_retake_authorizations")
    op.drop_index("ix_assessment_retake_authorizations_student_id", table_name="assessment_retake_authorizations")
    op.drop_index("ix_assessment_retake_authorizations_id", table_name="assessment_retake_authorizations")
    op.drop_table("assessment_retake_authorizations")

    op.drop_constraint("ck_assessment_sessions_attempt_no", "assessment_sessions", type_="check")
    op.drop_index("uq_assessment_sessions_prepost_attempt_no", table_name="assessment_sessions")
    op.drop_constraint("fk_assessment_sessions_supersedes_session", "assessment_sessions", type_="foreignkey")
    op.drop_column("assessment_sessions", "official_for_reporting")
    op.drop_column("assessment_sessions", "supersedes_session_id")
    op.drop_column("assessment_sessions", "assessment_attempt_no")

    op.create_index(
        "uq_assessment_sessions_prepost_once",
        "assessment_sessions",
        ["student_id", "session_type"],
        unique=True,
        postgresql_where=sa.text("session_type IN ('pretest', 'posttest')"),
        sqlite_where=sa.text("session_type IN ('pretest', 'posttest')"),
    )
