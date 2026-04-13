"""
Telegram client manager for pyrogram integration.
"""

import logging
from datetime import datetime, UTC
from typing import Optional

from pyrogram import Client
from pyrogram.errors import AuthKeyUnregistered, SessionPasswordNeeded
from pyrogram.types import Message

from config import settings
from ollama.prompt_handler import create_prompt
from database.message_store import add_message

logger = logging.getLogger("alpha")


def _get_message_type(message: Message) -> str:
    if message.text:
        return "text"
    elif message.photo:
        return "photo"
    elif message.video:
        return "video"
    elif message.audio:
        return "audio"
    elif message.voice:
        return "voice"
    elif message.document:
        return "document"
    elif message.sticker:
        return "sticker"
    elif message.animation:
        return "animation"
    elif message.poll:
        return "poll"
    elif message.location:
        return "location"
    elif message.contact:
        return "contact"
    else:
        return "other"


def _should_respond_with_ai(message: Message) -> bool:
    if message.outgoing:
        return False

    if message.chat.type.value == "private":
        return True

    if message.reply_to_message and message.reply_to_message.outgoing:
        return True

    if message.text:
        text_lower = message.text.lower()
        trigger_keywords = ["bot", "ai", "help"]
        if any(keyword in text_lower for keyword in trigger_keywords):
            return True

    return False


async def _handle_new_message(client: Client, message: Message) -> None:
    try:
        message_data = {
            "message_id": message.id,
            "chat_id": message.chat.id,
            "chat_title": getattr(message.chat, "title", None)
            or getattr(message.chat, "first_name", "Private Chat"),
            "chat_type": message.chat.type.value if message.chat.type else "unknown",
            "sender_id": message.from_user.id
            if message.from_user and not message.outgoing
            else None,
            "receiver_id": message.chat.id if message.outgoing else None,
            "username": message.from_user.username if message.from_user else None,
            "first_name": message.from_user.first_name if message.from_user else None,
            "last_name": message.from_user.last_name if message.from_user else None,
            "text": message.text if message.text else message.caption,
            "message_type": _get_message_type(message),
            "date": message.date if message.date else datetime.now(UTC),
            "reply_to_message_id": message.reply_to_message.id
            if message.reply_to_message
            else None,
        }

        # Mark the current message (and all previous) as read
        await client.read_chat_history(chat_id=message.chat.id, max_id=message.id)

        await add_message(message_data)

        chat_name = message_data["chat_title"]
        user_name = message_data["first_name"] or message_data["username"] or "Unknown"
        text_preview = (
            (message_data["text"][:50] + "...")
            if message_data["text"] and len(message_data["text"]) > 50
            else message_data["text"]
        )

        logger.info(
            f"Received {message_data['message_type']} from {user_name} in {chat_name}: {text_preview}"
        )

        ollama = getattr(client, "ollama_manager", None)
        if ollama and message_data["text"] and _should_respond_with_ai(message):
            reply_context = (
                message.reply_to_message.text if message.reply_to_message else None
            )
            response_text = await create_prompt(
                ollama,
                message_data["text"],
                reply_context,
            )
            if response_text:
                # sending the response here
                sent = await message.reply_text(response_text)
                logger.info(f"Sent response: {response_text[:50]}...")
                await add_message(
                    {
                        "message_id": sent.id,
                        "chat_id": sent.chat.id,
                        "chat_title": getattr(sent.chat, "title", None)
                        or getattr(sent.chat, "first_name", "Private Chat"),
                        "chat_type": sent.chat.type.value
                        if sent.chat.type
                        else "unknown",
                        "sender_id": None,
                        "receiver_id": sent.chat.id,
                        "username": None,
                        "first_name": None,
                        "last_name": None,
                        "text": response_text,
                        "message_type": "text",
                        "date": sent.date if sent.date else datetime.now(UTC),
                        "reply_to_message_id": message.id,
                    }
                )

    except Exception as e:
        logger.error(f"Error handling message {message.id}: {e}", exc_info=True)


class TelegramClientManager:
    """
    Manages the pyrogram client lifecycle and connection state.
    """

    def __init__(self):
        self.client: Optional[Client] = None
        self._running = False
        self._user_id: Optional[int] = None
        self._username: Optional[str] = None

    async def _authenticate(self) -> str:
        """
        Run interactive authentication and return the session string.
        """
        logger.info(
            "No session string found — starting interactive authentication, this will prompt for phone number and OTA passwd or token."
        )

        auth_client = Client(
            name=settings.TELEGRAM_SESSION_NAME,
            api_id=int(settings.TELEGRAM_API_ID),
            api_hash=settings.TELEGRAM_API_HASH,
            in_memory=True,
        )

        await auth_client.start()

        me = await auth_client.get_me()
        session_string = await auth_client.export_session_string()

        logger.info(f"Authentication successful as @{me.username} (ID: {me.id})")
        logger.info(
            f"Save this session string to TELEGRAM_SESSION_STRING:\n{session_string}"
        )

        await auth_client.stop()

        return session_string

    async def start(self) -> None:
        """
        Start the Telegram client and connect to Telegram.

        If TELEGRAM_SESSION_STRING is not set, runs the interactive auth workflow first.

        Raises:
            RuntimeError: If credentials are missing or connection fails
        """
        if self._running:
            logger.warning("Telegram client is already running")
            return

        if (
            not settings.TELEGRAM_SESSION_NAME
            or not settings.TELEGRAM_API_ID
            or not settings.TELEGRAM_API_HASH
        ):
            raise RuntimeError(
                "TELEGRAM_SESSION_NAME, TELEGRAM_API_ID, and TELEGRAM_API_HASH must be set"
            )

        session_string = settings.TELEGRAM_SESSION_STRING
        if not session_string:
            session_string = await self._authenticate()

        self.client = Client(
            name=settings.TELEGRAM_SESSION_NAME,
            api_id=int(settings.TELEGRAM_API_ID),
            api_hash=settings.TELEGRAM_API_HASH,
            session_string=session_string,
        )

        # the callback for incoming messages
        self.client.on_message()(_handle_new_message)

        try:
            await self.client.start()
            self._running = True

            me = await self.client.get_me()
            self._user_id = me.id
            self._username = me.username

            logger.info(
                f"Telegram client started successfully as @{self._username} (ID: {self._user_id})"
            )

        except AuthKeyUnregistered:
            logger.error("Session is invalid or expired. Please re-authenticate.")
            raise

        except SessionPasswordNeeded:
            logger.error(
                "Two-factor authentication is enabled. Please authenticate using the auth.py script."
            )
            raise

        except Exception as e:
            logger.error(f"Failed to start Telegram client: {e}")
            raise

    async def stop(self) -> None:
        """Gracefully stop the Telegram client."""
        if not self._running or not self.client:
            logger.warning("Telegram client is not running")
            return

        try:
            logger.info("Stopping Telegram client...")
            await self.client.stop()
            self._running = False
            self._user_id = None
            self._username = None
            logger.info("Telegram client stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping Telegram client: {e}", exc_info=True)
            raise

    def is_running(self) -> bool:
        return self._running

    def get_user_id(self) -> Optional[int]:
        return self._user_id

    def get_username(self) -> Optional[str]:
        return self._username
