"""
ChatterMate - Telegram Service
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

from typing import Optional

import httpx

from app.core.logger import get_logger

logger = get_logger(__name__)

# Maximum message length allowed by the Telegram Bot API
TELEGRAM_MAX_MESSAGE_LENGTH = 4096


class TelegramService:
    """Async service for interacting with the Telegram Bot API."""

    BASE_URL = "https://api.telegram.org"

    async def verify_token(self, bot_token: str) -> dict:
        """Verify a bot token and return bot info via getMe."""
        url = f"{self.BASE_URL}/bot{bot_token}/getMe"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10)
            data = response.json()
            if not data.get("ok"):
                description = data.get("description", "Unknown error")
                logger.error(f"Telegram getMe failed: {description}")
                raise ValueError(f"Invalid bot token: {description}")
            return data["result"]

    async def set_webhook(
        self,
        bot_token: str,
        webhook_url: str,
        secret_token: str,
    ) -> bool:
        """Set the webhook URL for the bot."""
        url = f"{self.BASE_URL}/bot{bot_token}/setWebhook"
        payload = {
            "url": webhook_url,
            "secret_token": secret_token,
            "allowed_updates": ["message"],
            "drop_pending_updates": True,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10)
            data = response.json()
            if not data.get("ok"):
                description = data.get("description", "Unknown error")
                logger.error(f"Telegram setWebhook failed: {description}")
                return False
            logger.info(f"Telegram webhook set successfully: {webhook_url}")
            return True

    async def delete_webhook(self, bot_token: str) -> bool:
        """Delete the webhook for the bot."""
        url = f"{self.BASE_URL}/bot{bot_token}/deleteWebhook"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, timeout=10)
            data = response.json()
            if not data.get("ok"):
                description = data.get("description", "Unknown error")
                logger.error(f"Telegram deleteWebhook failed: {description}")
                return False
            logger.info("Telegram webhook deleted successfully")
            return True

    async def send_message(
        self,
        bot_token: str,
        chat_id: int,
        text: str,
        parse_mode: Optional[str] = None,
    ) -> dict:
        """Send a text message to a Telegram chat."""
        url = f"{self.BASE_URL}/bot{bot_token}/sendMessage"

        # Truncate text to Telegram's maximum message length
        if len(text) > TELEGRAM_MAX_MESSAGE_LENGTH:
            text = text[:TELEGRAM_MAX_MESSAGE_LENGTH - 3] + "..."

        payload: dict = {
            "chat_id": chat_id,
            "text": text,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10)
            data = response.json()
            if not data.get("ok"):
                description = data.get("description", "Unknown error")
                logger.error(f"Telegram sendMessage failed: {description}")
                raise ValueError(f"Failed to send message: {description}")
            return data["result"]

    async def send_typing(self, bot_token: str, chat_id: int) -> bool:
        """Send a typing indicator to a Telegram chat."""
        url = f"{self.BASE_URL}/bot{bot_token}/sendChatAction"
        payload = {
            "chat_id": chat_id,
            "action": "typing",
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10)
            data = response.json()
            if not data.get("ok"):
                logger.warning(f"Telegram sendChatAction failed: {data.get('description')}")
                return False
            return True


# Singleton instance
telegram_service = TelegramService()
