"""audio review and session score

Revision ID: 0003_audio_review
Revises: 0002_content_models
Create Date: 2026-08-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_audio_review'
down_revision = '0002_content_models'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add columns to assessment_sessions
    op.add_column('assessment_sessions', sa.Column('final_score', sa.Float(), nullable=True))
    op.add_column('assessment_sessions', sa.Column('assigned_level', sa.Integer(), nullable=True))

    # Create audio_reviews table
    op.create_table(
        'audio_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('reviewer_id', sa.Integer(), nullable=False),
        sa.Column('target_units', sa.Integer(), nullable=False),
        sa.Column('deletions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('substitutions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('insertions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rubric_score', sa.Float(), nullable=False),
        sa.Column('pronunciation_notes', sa.String(), nullable=True),
        sa.Column('fluency_notes', sa.String(), nullable=True),
        sa.Column('time_notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['submission_id'], ['audio_submissions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audio_reviews_id'), 'audio_reviews', ['id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_audio_reviews_id'), table_name='audio_reviews')
    op.drop_table('audio_reviews')
    
    op.drop_column('assessment_sessions', 'assigned_level')
    op.drop_column('assessment_sessions', 'final_score')
