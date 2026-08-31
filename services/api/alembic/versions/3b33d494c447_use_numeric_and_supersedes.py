"""use_numeric_and_supersedes

Revision ID: 3b33d494c447
Revises: 0003_audio_review
Create Date: 2026-08-11 01:22:17.279718

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b33d494c447'
down_revision: Union[str, Sequence[str], None] = '0003_audio_review'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. scoring_rules
    op.alter_column('scoring_rules', 'max_raw_score',
                    existing_type=sa.Float(),
                    type_=sa.Numeric(precision=10, scale=2),
                    existing_nullable=False,
                    postgresql_using="max_raw_score::numeric")

    # 2. assessment_sessions
    op.alter_column('assessment_sessions', 'final_score',
                    existing_type=sa.Float(),
                    type_=sa.Numeric(precision=10, scale=4),
                    existing_nullable=True,
                    postgresql_using="final_score::numeric")

    # 3. audio_submissions
    op.alter_column('audio_submissions', 'duration_seconds',
                    existing_type=sa.Float(),
                    type_=sa.Numeric(precision=10, scale=2),
                    existing_nullable=True,
                    postgresql_using="duration_seconds::numeric")

    # 4. audio_reviews
    op.alter_column('audio_reviews', 'rubric_score',
                    existing_type=sa.Float(),
                    type_=sa.Numeric(precision=10, scale=4),
                    existing_nullable=False,
                    postgresql_using="rubric_score::numeric")
                    
    op.add_column('audio_reviews', sa.Column('supersedes_review_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_audio_reviews_supersedes', 'audio_reviews', 'audio_reviews', ['supersedes_review_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_audio_reviews_supersedes', 'audio_reviews', type_='foreignkey')
    op.drop_column('audio_reviews', 'supersedes_review_id')
    
    op.alter_column('audio_reviews', 'rubric_score',
                    existing_type=sa.Numeric(precision=10, scale=4),
                    type_=sa.Float(),
                    existing_nullable=False,
                    postgresql_using="rubric_score::double precision")

    op.alter_column('audio_submissions', 'duration_seconds',
                    existing_type=sa.Numeric(precision=10, scale=2),
                    type_=sa.Float(),
                    existing_nullable=True,
                    postgresql_using="duration_seconds::double precision")

    op.alter_column('assessment_sessions', 'final_score',
                    existing_type=sa.Numeric(precision=10, scale=4),
                    type_=sa.Float(),
                    existing_nullable=True,
                    postgresql_using="final_score::double precision")

    op.alter_column('scoring_rules', 'max_raw_score',
                    existing_type=sa.Numeric(precision=10, scale=2),
                    type_=sa.Float(),
                    existing_nullable=False,
                    postgresql_using="max_raw_score::double precision")
