"""
ChatterMate - Telegram API
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

import secrets
import traceback
import uuid
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth import get_current_organization
from app.core.config import settings
from app.core.logger import get_logger
from app.core.security import decrypt_api_key, encrypt_api_key
from app.database import get_db
from app.models.organization import Organization
from app.models.schemas.telegram import (
    TelegramConfigResponse,
    TelegramConnectRequest,
    TelegramStatusResponse,
)
from app.repositories.telegram import TelegramRepository
from app.services.telegram_service import telegram_service

router = APIRouter()
logger = get_logger(__name__)


# ==================== Management Endpoints (JWT auth required) ====================


@router.post("/connect", response_model=TelegramConfigResponse)
async def connect_telegram_bot(
    request: TelegramConnectRequest,
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Connect a Telegram bot to an agent."""
    try:
        # Validate the bot token via Telegram API
        bot_info = await telegram_service.verify_token(request.bot_token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    bot_username = bot_info.get("username", "")
    bot_display_name = bot_info.get("first_name")

    # Validate agent_id
    try:
        agent_uuid = UUID(request.agent_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid agent ID format")

    telegram_repo = TelegramRepository(db)

    # Check if bot is already connected for this org
    existing_configs = telegram_repo.get_configs_by_org(organization.id)
    for cfg in existing_configs:
        if cfg.bot_username == bot_username:
            raise HTTPException(
                status_code=400,
                detail=f"Bot @{bot_username} is already connected to this organization",
            )

    # Encrypt token and generate webhook secret
    encrypted_token = encrypt_api_key(request.bot_token)
    webhook_secret = secrets.token_urlsafe(32)

    try:
        config = telegram_repo.create_config(
            organization_id=organization.id,
            agent_id=agent_uuid,
            bot_token_encrypted=encrypted_token,
            bot_username=bot_username,
            bot_display_name=bot_display_name,
            webhook_secret=webhook_secret,
        )
    except Exception as e:
        logger.error(f"Failed to create Telegram config: {e}")
        raise HTTPException(status_code=500, detail="Failed to save bot configuration")

    # Set webhook with Telegram API
    webhook_url = f"{settings.BACKEND_URL}{settings.API_V1_STR}/telegram/webhook/{config.id}"
    webhook_set = await telegram_service.set_webhook(
        bot_token=request.bot_token,
        webhook_url=webhook_url,
        secret_token=webhook_secret,
    )

    if not webhook_set:
        # Rollback the config since webhook failed
        telegram_repo.delete_config(config.id)
        raise HTTPException(status_code=500, detail="Failed to set Telegram webhook")

    logger.info(
        f"Telegram bot @{bot_username} connected for org {organization.id}, "
        f"agent {request.agent_id}, config {config.id}"
    )

    return TelegramConfigResponse(
        id=config.id,
        organization_id=str(config.organization_id),
        agent_id=str(config.agent_id),
        bot_username=config.bot_username,
        bot_display_name=config.bot_display_name,
        is_active=config.is_active,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.get("/status", response_model=TelegramStatusResponse)
async def telegram_status(
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Check Telegram connection status for the current organization."""
    telegram_repo = TelegramRepository(db)
    configs = telegram_repo.get_configs_by_org(organization.id)

    config_responses = [
        TelegramConfigResponse(
            id=cfg.id,
            organization_id=str(cfg.organization_id),
            agent_id=str(cfg.agent_id),
            bot_username=cfg.bot_username,
            bot_display_name=cfg.bot_display_name,
            is_active=cfg.is_active,
            created_at=cfg.created_at,
            updated_at=cfg.updated_at,
        )
        for cfg in configs
    ]

    return TelegramStatusResponse(
        connected=len(config_responses) > 0,
        configs=config_responses,
    )


@router.delete("/{config_id}")
async def disconnect_telegram_bot(
    config_id: int,
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Disconnect a Telegram bot by deleting its configuration."""
    telegram_repo = TelegramRepository(db)
    config = telegram_repo.get_config_by_id(config_id)

    if not config:
        raise HTTPException(status_code=404, detail="Telegram bot configuration not found")

    if config.organization_id != organization.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this configuration")

    # Delete webhook from Telegram API
    try:
        bot_token = decrypt_api_key(config.bot_token_encrypted)
        await telegram_service.delete_webhook(bot_token)
    except Exception as e:
        logger.warning(f"Failed to delete Telegram webhook for config {config_id}: {e}")
        # Continue with local cleanup even if webhook deletion fails

    deleted = telegram_repo.delete_config(config_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete configuration")

    logger.info(f"Telegram bot @{config.bot_username} disconnected for org {organization.id}")
    return {"message": "Telegram bot disconnected successfully"}


# ==================== Webhook Endpoint (NO auth, uses secret token) ====================


@router.post("/webhook/{config_id}")
async def telegram_webhook(
    config_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Handle incoming Telegram webhook updates."""
    telegram_repo = TelegramRepository(db)
    config = telegram_repo.get_config_by_id(config_id)

    if not config:
        logger.warning(f"Telegram webhook received for unknown config_id: {config_id}")
        raise HTTPException(status_code=404, detail="Configuration not found")

    if not config.is_active:
        logger.info(f"Telegram webhook received for inactive config_id: {config_id}")
        return {"ok": True}

    # Verify the secret token header
    secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if secret_token != config.webhook_secret:
        logger.warning(f"Telegram webhook secret mismatch for config_id: {config_id}")
        raise HTTPException(status_code=401, detail="Invalid secret token")

    # Parse the update body
    try:
        update = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Acknowledge immediately, process in background
    background_tasks.add_task(_process_telegram_update, update, config.id, db)

    return {"ok": True}


async def _process_telegram_update(update: dict, config_id: int, db: Session) -> None:
    """Process a Telegram update in the background."""
    try:
        # Re-fetch config inside background task to avoid detached session issues
        telegram_repo = TelegramRepository(db)
        config = telegram_repo.get_config_by_id(config_id)
        if not config:
            logger.error(f"Config {config_id} not found during background processing")
            return

        bot_token = decrypt_api_key(config.bot_token_encrypted)

        # Skip if no message field
        message = update.get("message")
        if not message:
            logger.debug(f"Telegram update has no message field, skipping")
            return

        chat = message.get("chat", {})
        chat_id = chat.get("id")
        chat_type = chat.get("type")

        # Only handle private chats (ignore groups, supergroups, channels)
        if chat_type != "private":
            logger.debug(f"Ignoring non-private chat type: {chat_type}")
            return

        # Extract sender info
        from_user = message.get("from", {})
        telegram_user_id = from_user.get("id")
        first_name = from_user.get("first_name", "")
        last_name = from_user.get("last_name", "")
        display_name = f"{first_name} {last_name}".strip() or f"Telegram User {telegram_user_id}"

        # Extract text content
        text = message.get("text", "")

        # Handle non-text messages (photos, stickers, etc.)
        if not text:
            try:
                await telegram_service.send_message(
                    bot_token=bot_token,
                    chat_id=chat_id,
                    text="Sorry, I currently support text messages only.",
                )
            except Exception as e:
                logger.error(f"Failed to send unsupported content reply: {e}")
            return

        # Handle /start command
        if text.strip().startswith("/start"):
            bot_name = config.bot_display_name or config.bot_username
            welcome_text = (
                f"👋 Hello {first_name}! I'm {bot_name}.\n\n"
                f"Send me a message and I'll do my best to help you!"
            )
            try:
                await telegram_service.send_message(
                    bot_token=bot_token,
                    chat_id=chat_id,
                    text=welcome_text,
                )
            except Exception as e:
                logger.error(f"Failed to send welcome message: {e}")
            return

        # Process normal text message
        await _handle_chat_message(
            db=db,
            config=config,
            bot_token=bot_token,
            chat_id=chat_id,
            telegram_user_id=telegram_user_id,
            display_name=display_name,
            text=text,
        )

    except Exception as e:
        logger.error(f"Error processing Telegram update for config {config_id}: {e}")
        traceback.print_exc()


async def _handle_chat_message(
    db: Session,
    config,
    bot_token: str,
    chat_id: int,
    telegram_user_id: int,
    display_name: str,
    text: str,
) -> None:
    """Handle a normal text chat message from a Telegram user."""
    from app.agents.chat_agent import ChatAgent
    from app.repositories.ai_config import AIConfigRepository
    from app.repositories.customer import CustomerRepository
    from app.repositories.session_to_agent import SessionToAgentRepository

    org_id = config.organization_id
    agent_id = config.agent_id

    try:
        # Get or create customer
        customer_repo = CustomerRepository(db)
        telegram_email = f"{telegram_user_id}@telegram.user"
        customer = customer_repo.get_or_create_customer(
            email=telegram_email,
            organization_id=org_id,
            full_name=display_name,
        )

        # Get or create session
        session_repo = SessionToAgentRepository(db)
        session = session_repo.get_active_customer_session(
            customer.id, agent_id=agent_id
        )
        if not session:
            session_id = str(uuid.uuid4())
            session = session_repo.create_session(
                session_id=session_id,
                agent_id=str(agent_id),
                customer_id=str(customer.id),
                organization_id=str(org_id),
            )
        else:
            session_id = str(session.session_id)

        # Get AI config
        ai_config_repo = AIConfigRepository(db)
        ai_config = ai_config_repo.get_active_config(str(org_id))

        if not ai_config:
            logger.error(f"No AI config found for org {org_id}")
            await telegram_service.send_message(
                bot_token=bot_token,
                chat_id=chat_id,
                text="Sorry, I'm not properly configured yet. Please contact an administrator.",
            )
            return

        # Send typing indicator
        await telegram_service.send_typing(bot_token=bot_token, chat_id=chat_id)

        # Create ChatAgent and get response
        chat_agent = ChatAgent(
            api_key=decrypt_api_key(ai_config.encrypted_api_key),
            model_name=ai_config.model_name,
            model_type=ai_config.model_type.value,
            org_id=str(org_id),
            agent_id=str(agent_id),
            customer_id=str(customer.id),
            session_id=str(session.session_id),
        )

        response = await chat_agent.get_response(
            message=text,
            session_id=str(session.session_id),
            org_id=str(org_id),
            agent_id=str(agent_id),
            customer_id=str(customer.id),
        )

        # Send response — get_response() already handles message storage
        await telegram_service.send_message(
            bot_token=bot_token,
            chat_id=chat_id,
            text=response.message,
        )

    except Exception as e:
        logger.error(f"Error handling Telegram chat message: {e}")
        traceback.print_exc()

        # Send error message to user
        try:
            await telegram_service.send_message(
                bot_token=bot_token,
                chat_id=chat_id,
                text="Sorry, I encountered an error processing your request. Please try again.",
            )
        except Exception:
            pass
