"""Add relational prompt asset metadata linked to MinIO or local blobs."""

import sqlalchemy as sa

from alembic import op

revision = "20260331_0002"
down_revision = "20260331_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add prompt_assets table."""
    op.create_table(
        "prompt_assets",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "version_id",
            sa.String(length=36),
            sa.ForeignKey(
                "prompt_versions.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column(
            "storage_backend",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column("bucket", sa.String(length=255), nullable=False),
        sa.Column(
            "object_key",
            sa.String(length=1024),
            nullable=False,
        ),
        sa.Column(
            "content_type",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column("byte_size", sa.Integer(), nullable=True),
        sa.Column(
            "checksum_sha256",
            sa.String(length=64),
            nullable=True,
        ),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=False),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_prompt_assets_version_id",
        "prompt_assets",
        ["version_id"],
    )


def downgrade() -> None:
    """Drop prompt_assets table."""
    op.drop_index(
        "ix_prompt_assets_version_id",
        table_name="prompt_assets",
    )
    op.drop_table("prompt_assets")
