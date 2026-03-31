"""Initial promptdb schema."""

import sqlalchemy as sa

from alembic import op

revision = '20260331_0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the initial schema."""
    op.create_table(
        'prompts',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('namespace', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column(
            'created_at', sa.DateTime(timezone=False),
            nullable=False, server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            'namespace', 'name', name='uq_prompts_namespace_name',
        ),
    )
    op.create_table(
        'prompt_versions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column(
            'prompt_id', sa.String(length=36),
            sa.ForeignKey('prompts.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column(
            'user_version', sa.String(length=255), nullable=True,
        ),
        sa.Column('spec_json', sa.Text(), nullable=False),
        sa.Column('spec_hash', sa.String(length=64), nullable=False),
        sa.Column(
            'created_by', sa.String(length=255), nullable=True,
        ),
        sa.Column(
            'created_at', sa.DateTime(timezone=False),
            nullable=False, server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            'prompt_id', 'revision',
            name='uq_prompt_versions_prompt_revision',
        ),
    )
    op.create_table(
        'prompt_aliases',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column(
            'prompt_id', sa.String(length=36),
            sa.ForeignKey('prompts.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('alias', sa.String(length=255), nullable=False),
        sa.Column(
            'version_id', sa.String(length=36),
            sa.ForeignKey(
                'prompt_versions.id', ondelete='CASCADE',
            ),
            nullable=False,
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=False),
            nullable=False, server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            'prompt_id', 'alias',
            name='uq_prompt_aliases_prompt_alias',
        ),
    )


def downgrade() -> None:
    """Revert the initial schema."""
    op.drop_table('prompt_aliases')
    op.drop_table('prompt_versions')
    op.drop_table('prompts')
