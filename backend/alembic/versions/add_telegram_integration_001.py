"""Add Telegram bot integration table

Revision ID: add_telegram_integration_001
Revises: add_slack_integration_001
Create Date: 2026-06-12 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_telegram_integration_001'
down_revision: Union[str, None] = 'add_slack_integration_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create telegram_bot_configs table
    op.create_table('telegram_bot_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('agent_id', sa.UUID(), nullable=False),
        sa.Column('bot_token_encrypted', sa.String(), nullable=False),
        sa.Column('bot_username', sa.String(), nullable=False),
        sa.Column('bot_display_name', sa.String(), nullable=True),
        sa.Column('webhook_secret', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'bot_username', name='uq_telegram_bot_config_org_username')
    )
    op.create_index(op.f('ix_telegram_bot_configs_id'), 'telegram_bot_configs', ['id'], unique=False)
    op.create_index(op.f('ix_telegram_bot_configs_organization_id'), 'telegram_bot_configs', ['organization_id'], unique=False)
    op.create_index(op.f('ix_telegram_bot_configs_agent_id'), 'telegram_bot_configs', ['agent_id'], unique=False)
    op.create_index(op.f('ix_telegram_bot_configs_bot_username'), 'telegram_bot_configs', ['bot_username'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_telegram_bot_configs_bot_username'), table_name='telegram_bot_configs')
    op.drop_index(op.f('ix_telegram_bot_configs_agent_id'), table_name='telegram_bot_configs')
    op.drop_index(op.f('ix_telegram_bot_configs_organization_id'), table_name='telegram_bot_configs')
    op.drop_index(op.f('ix_telegram_bot_configs_id'), table_name='telegram_bot_configs')
    op.drop_table('telegram_bot_configs')
