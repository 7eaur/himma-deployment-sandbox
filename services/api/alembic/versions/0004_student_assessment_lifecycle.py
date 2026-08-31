"""student assessment lifecycle and durable idempotency

Revision ID: 0004_student_lifecycle
Revises: 3b33d494c447
Create Date: 2026-08-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0004_student_lifecycle"
down_revision = "3b33d494c447"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "students",
        sa.Column("grade_level", sa.Integer(), server_default="3", nullable=False),
    )
    op.add_column(
        "students",
        sa.Column("posttest_enabled", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column(
        "students",
        sa.Column("posttest_enabled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "students",
        sa.Column("posttest_enabled_by", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_students_posttest_enabled_by",
        "students",
        "users",
        ["posttest_enabled_by"],
        ["id"],
    )
    op.create_check_constraint(
        "ck_students_grade_level_third", "students", "grade_level = 3"
    )
    op.create_check_constraint(
        "ck_students_current_level", "students", "current_level BETWEEN 1 AND 3"
    )

    op.add_column(
        "assessment_sessions",
        sa.Column("elapsed_seconds", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "assessment_sessions",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "ck_assessment_sessions_type",
        "assessment_sessions",
        "session_type IN ('pretest', 'posttest', 'core')",
    )
    op.create_check_constraint(
        "ck_assessment_sessions_status",
        "assessment_sessions",
        "status IN ('in_progress', 'completed')",
    )
    op.create_check_constraint(
        "ck_assessment_sessions_elapsed",
        "assessment_sessions",
        "elapsed_seconds >= 0",
    )
    op.create_index(
        "uq_assessment_sessions_active_student",
        "assessment_sessions",
        ["student_id"],
        unique=True,
        postgresql_where=sa.text("status = 'in_progress'"),
    )
    op.create_index(
        "uq_assessment_sessions_prepost_once",
        "assessment_sessions",
        ["student_id", "session_type"],
        unique=True,
        postgresql_where=sa.text("session_type IN ('pretest', 'posttest')"),
    )

    op.add_column(
        "attempts",
        sa.Column("elapsed_seconds", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_unique_constraint(
        "uq_attempts_session_item", "attempts", ["session_id", "item_id"]
    )
    op.create_check_constraint(
        "ck_attempts_status", "attempts", "status IN ('in_progress', 'completed')"
    )
    op.create_check_constraint(
        "ck_attempts_elapsed", "attempts", "elapsed_seconds >= 0"
    )

    op.add_column(
        "attempt_responses",
        sa.Column("elapsed_seconds", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_unique_constraint(
        "uq_attempt_responses_attempt_step",
        "attempt_responses",
        ["attempt_id", "step_id"],
    )
    op.create_check_constraint(
        "ck_attempt_responses_elapsed",
        "attempt_responses",
        "elapsed_seconds >= 0",
    )

    op.create_table(
        "operation_idempotency",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_role", sa.String(length=50), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("operation", sa.String(length=100), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("response_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status_code", sa.Integer(), server_default="200", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "actor_role",
            "actor_id",
            "operation",
            "idempotency_key",
            name="uq_operation_idempotency_scope_key",
        ),
    )
    op.create_index(
        op.f("ix_operation_idempotency_id"),
        "operation_idempotency",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_operation_idempotency_id"), table_name="operation_idempotency"
    )
    op.drop_table("operation_idempotency")

    op.drop_constraint(
        "ck_attempt_responses_elapsed", "attempt_responses", type_="check"
    )
    op.drop_constraint(
        "uq_attempt_responses_attempt_step", "attempt_responses", type_="unique"
    )
    op.drop_column("attempt_responses", "elapsed_seconds")

    op.drop_constraint("ck_attempts_elapsed", "attempts", type_="check")
    op.drop_constraint("ck_attempts_status", "attempts", type_="check")
    op.drop_constraint("uq_attempts_session_item", "attempts", type_="unique")
    op.drop_column("attempts", "elapsed_seconds")

    op.drop_index(
        "uq_assessment_sessions_prepost_once", table_name="assessment_sessions"
    )
    op.drop_index(
        "uq_assessment_sessions_active_student", table_name="assessment_sessions"
    )
    op.drop_constraint(
        "ck_assessment_sessions_elapsed", "assessment_sessions", type_="check"
    )
    op.drop_constraint(
        "ck_assessment_sessions_status", "assessment_sessions", type_="check"
    )
    op.drop_constraint(
        "ck_assessment_sessions_type", "assessment_sessions", type_="check"
    )
    op.drop_column("assessment_sessions", "updated_at")
    op.drop_column("assessment_sessions", "elapsed_seconds")

    op.drop_constraint("ck_students_current_level", "students", type_="check")
    op.drop_constraint("ck_students_grade_level_third", "students", type_="check")
    op.drop_constraint(
        "fk_students_posttest_enabled_by", "students", type_="foreignkey"
    )
    op.drop_column("students", "posttest_enabled_by")
    op.drop_column("students", "posttest_enabled_at")
    op.drop_column("students", "posttest_enabled")
    op.drop_column("students", "grade_level")
