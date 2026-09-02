"""researcher supervisor notifications

Revision ID: 0010_researcher_notifications
Revises: 0009_assessment_retakes
"""
from alembic import op
import sqlalchemy as sa

revision = "0010_researcher_notifications"
down_revision = "0009_assessment_retakes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "researcher_notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("notification_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("message", sa.String(length=1000), nullable=False),
        sa.Column("href", sa.String(length=500), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=True),
        sa.Column("entity_id", sa.String(length=100), nullable=True),
        sa.Column("dedupe_key", sa.String(length=180), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("dedupe_key", name="uq_researcher_notifications_dedupe_key"),
    )
    op.create_index("ix_researcher_notifications_id", "researcher_notifications", ["id"])
    op.create_index("ix_researcher_notifications_notification_type", "researcher_notifications", ["notification_type"])
    op.create_index("ix_researcher_notifications_is_read", "researcher_notifications", ["is_read"])


def downgrade() -> None:
    op.drop_index("ix_researcher_notifications_is_read", table_name="researcher_notifications")
    op.drop_index("ix_researcher_notifications_notification_type", table_name="researcher_notifications")
    op.drop_index("ix_researcher_notifications_id", table_name="researcher_notifications")
    op.drop_table("researcher_notifications")
