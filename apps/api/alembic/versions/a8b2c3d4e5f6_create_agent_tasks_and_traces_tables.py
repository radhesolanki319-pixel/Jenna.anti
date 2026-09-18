"""create_agent_tasks_and_traces_tables

Revision ID: a8b2c3d4e5f6
Revises: f7a18b2c9d3e
Create Date: 2026-09-13 11:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a8b2c3d4e5f6'
down_revision: Union[str, None] = 'f7a18b2c9d3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create agent_tasks table
    op.create_table(
        'agent_tasks',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('parent_task_id', sa.Uuid(), nullable=True),
        sa.Column('agent_type', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), server_default='', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='CREATED', nullable=False),
        sa.Column('priority', sa.String(length=32), server_default='NORMAL', nullable=False),
        sa.Column('budget', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
        sa.Column('steps_executed', sa.Integer(), server_default='0', nullable=False),
        sa.Column('tokens_used', sa.Integer(), server_default='0', nullable=False),
        sa.Column('context_handoff', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
        sa.Column('result_summary', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('requires_confirmation', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('confirmation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['parent_task_id'], ['agent_tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_agent_tasks_user_id'), 'agent_tasks', ['user_id'], unique=False)
    op.create_index(op.f('ix_agent_tasks_parent_task_id'), 'agent_tasks', ['parent_task_id'], unique=False)
    op.create_index(op.f('ix_agent_tasks_agent_type'), 'agent_tasks', ['agent_type'], unique=False)
    op.create_index(op.f('ix_agent_tasks_status'), 'agent_tasks', ['status'], unique=False)
    op.create_index(op.f('ix_agent_tasks_updated_at'), 'agent_tasks', ['updated_at'], unique=False)
    op.create_index('ix_agent_tasks_user_status', 'agent_tasks', ['user_id', 'status'], unique=False)
    op.create_index('ix_agent_tasks_user_updated', 'agent_tasks', ['user_id', 'updated_at'], unique=False)

    # 2. Create agent_step_traces table
    op.create_table(
        'agent_step_traces',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('task_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('step_index', sa.Integer(), nullable=False),
        sa.Column('agent_type', sa.String(length=64), nullable=False),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='RUNNING', nullable=False),
        sa.Column('duration_ms', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('output_summary', sa.Text(), server_default='', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['agent_tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_agent_step_traces_task_id'), 'agent_step_traces', ['task_id'], unique=False)
    op.create_index(op.f('ix_agent_step_traces_user_id'), 'agent_step_traces', ['user_id'], unique=False)
    op.create_index('ix_step_traces_task_index', 'agent_step_traces', ['task_id', 'step_index'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_step_traces_task_index', table_name='agent_step_traces')
    op.drop_index(op.f('ix_agent_step_traces_user_id'), table_name='agent_step_traces')
    op.drop_index(op.f('ix_agent_step_traces_task_id'), table_name='agent_step_traces')
    op.drop_table('agent_step_traces')

    op.drop_index('ix_agent_tasks_user_updated', table_name='agent_tasks')
    op.drop_index('ix_agent_tasks_user_status', table_name='agent_tasks')
    op.drop_index(op.f('ix_agent_tasks_updated_at'), table_name='agent_tasks')
    op.drop_index(op.f('ix_agent_tasks_status'), table_name='agent_tasks')
    op.drop_index(op.f('ix_agent_tasks_agent_type'), table_name='agent_tasks')
    op.drop_index(op.f('ix_agent_tasks_parent_task_id'), table_name='agent_tasks')
    op.drop_index(op.f('ix_agent_tasks_user_id'), table_name='agent_tasks')
    op.drop_table('agent_tasks')
