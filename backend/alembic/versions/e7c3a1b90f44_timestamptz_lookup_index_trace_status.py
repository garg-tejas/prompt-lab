"""timezone-aware timestamps, eval lookup index, trace status

Revision ID: e7c3a1b90f44
Revises: d5b2f9c18e22
Create Date: 2026-10-02 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e7c3a1b90f44'
down_revision: Union[str, None] = 'd5b2f9c18e22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_COLUMNS = [
    ('users', 'created_at', False),
    ('users', 'updated_at', False),
    ('prompt_tags', 'created_at', False),
    ('prompts', 'created_at', False),
    ('prompts', 'updated_at', False),
    ('prompt_versions', 'created_at', False),
    ('datasets', 'created_at', False),
    ('dataset_rows', 'created_at', False),
    ('model_endpoints', 'created_at', False),
    ('eval_runs', 'created_at', False),
    ('eval_runs', 'completed_at', True),
    ('eval_results', 'created_at', False),
    ('metric_scores', 'created_at', False),
    ('ab_tests', 'created_at', False),
    ('ab_tests', 'completed_at', True),
    ('api_tokens', 'created_at', False),
    ('api_tokens', 'last_used_at', True),
    ('webhooks', 'created_at', False),
    ('webhook_deliveries', 'created_at', False),
    ('traces', 'created_at', False),
]


def _timestamptz(table: str, column: str, nullable: bool) -> None:
    op.alter_column(
        table,
        column,
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        existing_nullable=nullable,
        nullable=nullable,
    )


def upgrade() -> None:
    for table, column, nullable in _COLUMNS:
        _timestamptz(table, column, nullable)
    op.create_index(
        'ix_eval_runs_lookup',
        'eval_runs',
        ['prompt_id', 'dataset_id', 'model_id', 'status'],
    )
    op.add_column(
        'traces',
        sa.Column('status', sa.String(), nullable=False, server_default='stored'),
    )


def downgrade() -> None:
    op.drop_column('traces', 'status')
    op.drop_index('ix_eval_runs_lookup', table_name='eval_runs')
    for table, column, nullable in reversed(_COLUMNS):
        op.alter_column(
            table,
            column,
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
            existing_nullable=nullable,
            nullable=nullable,
        )
