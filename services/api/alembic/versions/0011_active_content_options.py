"""active content option lifecycle

Revision ID: 0011_active_content_options
Revises: 0010_researcher_notifications

Published student responses may reference historical ContentOption rows.  Instead
of deleting those rows when presentation contracts evolve, current choices are
marked active/inactive.  Student runtime relationships expose active choices
only while historical responses retain their original foreign keys.
"""
from alembic import op
import sqlalchemy as sa

revision = "0011_active_content_options"
down_revision = "0010_researcher_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "content_options",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index(
        "ix_content_options_step_active_order",
        "content_options",
        ["step_id", "is_active", "order_index"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_content_options_step_active_order", table_name="content_options")
    op.drop_column("content_options", "is_active")
