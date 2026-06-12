"""
ChatterMate - Telegram Repository
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

from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from app.models.telegram import TelegramBotConfig
from app.core.logger import get_logger

logger = get_logger(__name__)


class TelegramRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_config(
        self,
        organization_id: UUID,
        agent_id: UUID,
        bot_token_encrypted: str,
        bot_username: str,
        webhook_secret: str,
        bot_display_name: Optional[str] = None,
    ) -> TelegramBotConfig:
        """Create a new Telegram bot configuration."""
        try:
            config = TelegramBotConfig(
                organization_id=organization_id,
                agent_id=agent_id,
                bot_token_encrypted=bot_token_encrypted,
                bot_username=bot_username,
                bot_display_name=bot_display_name,
                webhook_secret=webhook_secret,
            )
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
            return config
        except Exception as e:
            logger.error(f"Error creating Telegram config: {str(e)}")
            self.db.rollback()
            raise

    def get_config_by_id(self, config_id: int) -> Optional[TelegramBotConfig]:
        """Get a Telegram bot configuration by ID."""
        try:
            return self.db.query(TelegramBotConfig).filter(
                TelegramBotConfig.id == config_id
            ).first()
        except Exception as e:
            logger.error(f"Error getting Telegram config by ID: {str(e)}")
            return None

    def get_configs_by_org(self, org_id: UUID) -> List[TelegramBotConfig]:
        """Get all Telegram bot configurations for an organization."""
        try:
            return self.db.query(TelegramBotConfig).filter(
                TelegramBotConfig.organization_id == org_id
            ).all()
        except Exception as e:
            logger.error(f"Error getting Telegram configs by org: {str(e)}")
            return []

    def get_config_by_agent(self, agent_id: UUID) -> Optional[TelegramBotConfig]:
        """Get a Telegram bot configuration by agent ID."""
        try:
            return self.db.query(TelegramBotConfig).filter(
                TelegramBotConfig.agent_id == agent_id
            ).first()
        except Exception as e:
            logger.error(f"Error getting Telegram config by agent: {str(e)}")
            return None

    def delete_config(self, config_id: int) -> bool:
        """Delete a Telegram bot configuration by ID."""
        try:
            config = self.db.query(TelegramBotConfig).filter(
                TelegramBotConfig.id == config_id
            ).first()
            if not config:
                return False
            self.db.delete(config)
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting Telegram config: {str(e)}")
            self.db.rollback()
            return False
