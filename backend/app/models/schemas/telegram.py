"""
ChatterMate - Telegram Schemas
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

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TelegramConnectRequest(BaseModel):
    """Request schema for connecting a Telegram bot."""
    bot_token: str
    agent_id: str


class TelegramConfigResponse(BaseModel):
    """Response schema for a Telegram bot configuration."""
    id: int
    organization_id: str
    agent_id: str
    bot_username: str
    bot_display_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TelegramStatusResponse(BaseModel):
    """Response schema for Telegram connection status."""
    connected: bool
    configs: List[TelegramConfigResponse] = []
