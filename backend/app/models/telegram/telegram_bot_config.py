"""
ChatterMate - Telegram Bot Config Model
Copyright (C) 2024 ChatterMate

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class TelegramBotConfig(Base):
    """Model for Telegram bot configuration linking org + agent + bot."""
    __tablename__ = "telegram_bot_configs"

    # Unique constraint on (organization_id, bot_username) to prevent duplicate bot connections
    __table_args__ = (
        UniqueConstraint('organization_id', 'bot_username', name='uq_telegram_bot_config_org_username'),
    )

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    bot_token_encrypted = Column(String, nullable=False)  # Encrypted via encrypt_api_key
    bot_username = Column(String, nullable=False, index=True)  # From getMe, without @
    bot_display_name = Column(String, nullable=True)  # Human-readable bot name
    webhook_secret = Column(String, nullable=False)  # Random string for webhook verification

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="telegram_bot_configs")
    agent = relationship("Agent", back_populates="telegram_configs")
