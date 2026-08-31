"""Content models

Revision ID: 0002_content_models
Revises: 0001_initial
Create Date: 2026-08-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '0002_content_models'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. create skills table
    op.create_table(
        'skills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('skill_key', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('level_id', sa.Integer(), nullable=False),
        sa.Column('canonical_skill_id', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_skills_id'), 'skills', ['id'], unique=False)
    op.create_index(op.f('ix_skills_skill_key'), 'skills', ['skill_key'], unique=True)

    # 2. create content_releases table
    op.create_table(
        'content_releases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('released_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version')
    )
    op.create_index(op.f('ix_content_releases_id'), 'content_releases', ['id'], unique=False)

    # 3. create content_items table
    op.create_table(
        'content_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stable_key', sa.String(length=100), nullable=False),
        sa.Column('kind', sa.String(length=50), nullable=False),
        sa.Column('level_id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.Column('interaction_type', sa.String(length=50), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('template_data', sa.JSON().with_variant(postgresql.JSONB, 'postgresql'), nullable=True),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_items_id'), 'content_items', ['id'], unique=False)
    op.create_index(op.f('ix_content_items_stable_key'), 'content_items', ['stable_key'], unique=True)

    # 4. create content_steps table
    op.create_table(
        'content_steps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('prompt_text', sa.String(), nullable=False),
        sa.Column('expected_reading_text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['content_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_steps_id'), 'content_steps', ['id'], unique=False)

    # 5. create content_options table
    op.create_table(
        'content_options',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('step_id', sa.Integer(), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['step_id'], ['content_steps.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_options_id'), 'content_options', ['id'], unique=False)

    # 6. create content_asset_links table
    op.create_table(
        'content_asset_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=True),
        sa.Column('step_id', sa.Integer(), nullable=True),
        sa.Column('manifest_asset_id', sa.String(length=200), nullable=False),
        sa.Column('asset_type', sa.String(length=50), nullable=False),
        sa.Column('usage_context', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['content_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['step_id'], ['content_steps.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_asset_links_id'), 'content_asset_links', ['id'], unique=False)

    # 7. create scoring policies
    op.create_table(
        'scoring_policies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version')
    )
    op.create_index(op.f('ix_scoring_policies_id'), 'scoring_policies', ['id'], unique=False)

    op.create_table(
        'scoring_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('policy_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('max_raw_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('rubric', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['content_items.id'], ),
        sa.ForeignKeyConstraint(['policy_id'], ['scoring_policies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scoring_rules_id'), 'scoring_rules', ['id'], unique=False)

    # 8. create assessment tables
    op.create_table(
        'assessment_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('session_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='in_progress'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assessment_sessions_id'), 'assessment_sessions', ['id'], unique=False)

    op.create_table(
        'attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='in_progress'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['content_items.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['assessment_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_attempts_id'), 'attempts', ['id'], unique=False)

    op.create_table(
        'attempt_responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('attempt_id', sa.Integer(), nullable=False),
        sa.Column('step_id', sa.Integer(), nullable=False),
        sa.Column('selected_option_id', sa.Integer(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['attempt_id'], ['attempts.id'], ),
        sa.ForeignKeyConstraint(['selected_option_id'], ['content_options.id'], ),
        sa.ForeignKeyConstraint(['step_id'], ['content_steps.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_attempt_responses_id'), 'attempt_responses', ['id'], unique=False)

    op.create_table(
        'audio_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('response_id', sa.Integer(), nullable=False),
        sa.Column('storage_key', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='uploaded'),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['response_id'], ['attempt_responses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audio_submissions_id'), 'audio_submissions', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_audio_submissions_id'), table_name='audio_submissions')
    op.drop_table('audio_submissions')
    op.drop_index(op.f('ix_attempt_responses_id'), table_name='attempt_responses')
    op.drop_table('attempt_responses')
    op.drop_index(op.f('ix_attempts_id'), table_name='attempts')
    op.drop_table('attempts')
    op.drop_index(op.f('ix_assessment_sessions_id'), table_name='assessment_sessions')
    op.drop_table('assessment_sessions')
    
    op.drop_index(op.f('ix_scoring_rules_id'), table_name='scoring_rules')
    op.drop_table('scoring_rules')
    op.drop_index(op.f('ix_scoring_policies_id'), table_name='scoring_policies')
    op.drop_table('scoring_policies')

    op.drop_index(op.f('ix_content_asset_links_id'), table_name='content_asset_links')
    op.drop_table('content_asset_links')
    op.drop_index(op.f('ix_content_options_id'), table_name='content_options')
    op.drop_table('content_options')
    op.drop_index(op.f('ix_content_steps_id'), table_name='content_steps')
    op.drop_table('content_steps')
    
    op.drop_index(op.f('ix_content_items_stable_key'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_id'), table_name='content_items')
    op.drop_table('content_items')
    op.drop_index(op.f('ix_content_releases_id'), table_name='content_releases')
    op.drop_table('content_releases')
    op.drop_index(op.f('ix_skills_skill_key'), table_name='skills')
    op.drop_index(op.f('ix_skills_id'), table_name='skills')
    op.drop_table('skills')
