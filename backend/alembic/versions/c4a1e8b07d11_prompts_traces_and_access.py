"""system prompts, dataset extras, tokens, webhooks, traces

Revision ID: c4a1e8b07d11
Revises: e82228d56377
Create Date: 2026-10-02 12:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4a1e8b07d11"
down_revision: Union[str, None] = "e82228d56377"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("prompt_versions", sa.Column("system_content", sa.Text(), nullable=True))
    op.add_column("dataset_rows", sa.Column("extras", sa.JSON(), nullable=True))
    op.create_table(
        "api_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("token_prefix", sa.String(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_api_tokens_token_hash", "api_tokens", ["token_hash"], unique=True)
    op.create_table(
        "webhooks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("secret", sa.String(), nullable=False),
        sa.Column("events", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "traces",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("prompt_id", sa.UUID(), nullable=True),
        sa.Column("prompt_version_id", sa.UUID(), nullable=True),
        sa.Column("inputs", sa.JSON(), nullable=True),
        sa.Column("output", sa.Text(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("scores", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["prompt_id"], ["prompts.id"]),
        sa.ForeignKeyConstraint(["prompt_version_id"], ["prompt_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("traces")
    op.drop_table("webhooks")
    op.drop_index("ix_api_tokens_token_hash", table_name="api_tokens")
    op.drop_table("api_tokens")
    op.drop_column("dataset_rows", "extras")
    op.drop_column("prompt_versions", "system_content")
