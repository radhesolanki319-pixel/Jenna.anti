"""add_memory_lifecycle_and_supersession

Revision ID: f7a18b2c9d3e
Revises: e6fccb4c62d2
Create Date: 2026-09-13 05:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7a18b2c9d3e'
down_revision: Union[str, None] = 'e6fccb4c62d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to memories
    op.add_column('memories', sa.Column('conversation_id', sa.Uuid(), nullable=True))
    op.add_column('memories', sa.Column('superseded_by_id', sa.Uuid(), nullable=True))
    op.add_column('memories', sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False))
    op.add_column('memories', sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True))

    # Add foreign keys
    op.create_foreign_key(
        'fk_memories_conversation_id',
        'memories',
        'conversations',
        ['conversation_id'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_memories_superseded_by_id',
        'memories',
        'memories',
        ['superseded_by_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Add indexes
    op.create_index('ix_memories_conversation_id', 'memories', ['conversation_id'], unique=False)
    op.create_index('ix_memories_superseded_by_id', 'memories', ['superseded_by_id'], unique=False)
    op.create_index('ix_memories_status', 'memories', ['status'], unique=False)
    op.create_index('ix_memories_user_status', 'memories', ['user_id', 'status'], unique=False)
    op.create_index('ix_memories_user_type_status', 'memories', ['user_id', 'memory_type', 'status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_memories_user_type_status', table_name='memories')
    op.drop_index('ix_memories_user_status', table_name='memories')
    op.drop_index('ix_memories_status', table_name='memories')
    op.drop_index('ix_memories_superseded_by_id', table_name='memories')
    op.drop_index('ix_memories_conversation_id', table_name='memories')

    op.drop_constraint('fk_memories_superseded_by_id', 'memories', type_='foreignkey')
    op.drop_constraint('fk_memories_conversation_id', 'memories', type_='foreignkey')

    op.drop_column('memories', 'archived_at')
    op.drop_column('memories', 'status')
    op.drop_column('memories', 'superseded_by_id')
    op.drop_column('memories', 'conversation_id')
