"""
Pyrogram Client subclass with typed Ollama integration and message handling.
"""

import asyncio
import logging
import os
import random
from datetime import datetime, UTC

from pyrogram import Client
from pyrogram.enums import ChatAction
from pyrogram.types import Message

from config import settings
from database.message_store import add_message, get_chat_history
from ollama.ollama_client_manager import OllamaClientManager
from ollama.prompt_handler import create_prompt
from telegram.utils import get_message_type, should_respond_with_ai

logger = logging.getLogger("alpha")


class TelegramClient(Client):
    """
    Pyrogram Client with a typed ollama_manager attribute and built-in message handling.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ollama_manager: OllamaClientManager | None = None
        self.on_message()(self._handle_new_message)

    async def _handle_new_message(
        self, _client: "TelegramClient", message: Message
    ) -> None:
        try:
            _media = (
                message.photo
                or message.video
                or message.audio
                or message.voice
                or message.document
                or message.sticker
                or message.animation
            )

            file_path = None
            if _media:
                os.makedirs(settings.TELEGRAM_MEDIA_DIR, exist_ok=True)
                downloaded = await self.download_media(
                    message, file_name=settings.TELEGRAM_MEDIA_DIR + "/"
                )
                if downloaded:
                    file_path = downloaded

            message_data = {
                "message_id": message.id,
                "chat_id": message.chat.id,
                "chat_title": getattr(message.chat, "title", None)
                or getattr(message.chat, "first_name", "Private Chat"),
                "chat_type": message.chat.type.value
                if message.chat.type
                else "unknown",
                "sender_id": message.from_user.id
                if message.from_user and not message.outgoing
                else None,
                "receiver_id": message.chat.id if message.outgoing else None,
                "username": message.from_user.username if message.from_user else None,
                "first_name": message.from_user.first_name
                if message.from_user
                else None,
                "last_name": message.from_user.last_name if message.from_user else None,
                "text": message.text if message.text else message.caption,
                "message_type": get_message_type(message),
                "date": message.date if message.date else datetime.now(UTC),
                "reply_to_message_id": message.reply_to_message.id
                if message.reply_to_message
                else None,
                "file_id": _media.file_id if _media else None,
                "file_path": file_path,
            }

            flag_read_task = asyncio.create_task(self._flag_read(message.chat.id, message.id))

            await add_message(message_data)

            chat_name = message_data["chat_title"]
            user_name = (
                message_data["first_name"] or message_data["username"] or "Unknown"
            )
            text = message_data["text"]
            text_preview = (text[:50] + "...") if text else text

            logger.info(
                f"Received {message_data['message_type']} from {user_name} in {chat_name}: {text_preview}"
            )

            if (
                self.ollama_manager
                and message_data["text"]
                and should_respond_with_ai(message)
            ):
                reply_context = (
                    message.reply_to_message.text if message.reply_to_message else None
                )
                prior_messages = await get_chat_history(message.chat.id, limit=20)
                history = [
                    {
                        "role": "assistant" if m.sender_id is None else "user",
                        "content": m.text,
                    }
                    for m in prior_messages
                ]
                messages = await create_prompt(
                    message_data["text"],
                    history=history,
                    reply_context=reply_context,
                )
                result = await self.ollama_manager.chat(messages=messages)
                response_text = result.get("message", {}).get("content") or None
                if response_text:
                    await flag_read_task
                    await self._flag_typing(message.chat.id, response_text)
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

        except Exception as ex:
            logger.error(f"Error handling message {message.id}: {ex}", exc_info=True)

    async def _flag_read(self, chat_id: int, max_id: int) -> None:
        """Mark messages as read after a random human-like delay."""
        await asyncio.sleep(random.uniform(2, 20))
        try:
            await self.read_chat_history(chat_id=chat_id, max_id=max_id)
        except Exception as e:
            logger.warning(f"Failed to mark chat {chat_id} as read: {e}")

    async def _flag_typing(self, chat_id: int, response_text: str) -> None:
        """Show a typing indicator for a duration proportional to the response length."""
        word_count = len(response_text.split())
        # ~0.2 s per word, 1.5 s baseline, capped at 12 s
        typing_seconds = min(1.5 + word_count * 0.9, 12.0)
        elapsed = 0.0
        while elapsed < typing_seconds:
            await self.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            # Telegram's typing indicator expires after ~5 s, refresh every 4 s
            tick = min(4.0, typing_seconds - elapsed)
            await asyncio.sleep(tick)
            elapsed += tick
