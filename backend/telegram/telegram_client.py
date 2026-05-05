"""
Pyrogram Client subclass with typed Ollama integration and message handling.
"""

import asyncio
import logging
import os
import random
import re
from datetime import datetime, UTC

from pyrogram import Client
from pyrogram.enums import ChatAction
from pyrogram.types import Message

from config import settings
from database.message_store import add_message, get_chat_history
from ollama.ollama_client_manager import OllamaClientManager
from ollama.prompt_handler import create_prompt
from telegram.chat_state import ChatState
from telegram.utils import get_message_type, should_respond_with_ai

logger = logging.getLogger("alpha")


def _make_typo(word: str) -> str:
    """Return *word* with a single realistic keystroke-level typo."""
    pos = random.randint(1, len(word) - 2)
    match random.randint(0, 2):
        case 0:  # swap adjacent characters
            chars = list(word)
            chars[pos], chars[pos + 1] = chars[pos + 1], chars[pos]
            return "".join(chars)
        case 1:  # drop a character
            return word[:pos] + word[pos + 1:]
        case _:  # double a character
            return word[:pos] + word[pos] + word[pos:]


class TelegramClient(Client):
    """
    Pyrogram Client with a typed ollama_manager attribute and built-in message handling.

    Subsequent messages from the same chat are coalesced: any in-progress response is
    cancelled and a new one is generated that treats all accumulated message texts as a
    single input.  If the previous message's read receipt already fired, the next one is
    marked read immediately (short delay) instead of waiting the full human-like window.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ollama_manager: OllamaClientManager | None = None
        self._chats: dict[int, ChatState] = {}
        self.on_message()(self._handle_new_message)

    async def _handle_new_message(
        self, _client: "TelegramClient", message: Message
    ) -> None:
        try:
            message_data = await self._build_message_data(message)
            chat_id = message_data["chat_id"]
            state = self._chats.setdefault(chat_id, ChatState())

            self._schedule_read(state, chat_id, message.id)
            await add_message(message_data)
            self._log_received(message_data)

            if (
                self.ollama_manager
                and message_data["text"]
                and should_respond_with_ai(message)
            ):
                await self._schedule_response(state, message, message_data["text"])

        except Exception as ex:
            logger.error(f"Error handling message {message.id}: {ex}", exc_info=True)

    async def _build_message_data(self, message: Message) -> dict:
        """Download any media and return a normalised message dict."""
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

        return {
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
            "message_type": get_message_type(message),
            "date": message.date if message.date else datetime.now(UTC),
            "reply_to_message_id": message.reply_to_message.id
            if message.reply_to_message
            else None,
            "file_id": _media.file_id if _media else None,
            "file_path": file_path,
        }

    def _schedule_read(self, state: ChatState, chat_id: int, message_id: int) -> None:
        """Cancel any stale read task and start a new one for *message_id*."""
        state.schedule_read(self._flag_read(chat_id, message_id, state.read_delay))

    def _log_received(self, message_data: dict) -> None:
        text = message_data["text"]
        text_preview = (text[:50] + "...") if text else text
        user_name = message_data["first_name"] or message_data["username"] or "Unknown"
        logger.info(
            f"Received {message_data['message_type']} from {user_name}"
            f" in {message_data['chat_title']}: {text_preview}"
        )

    async def _schedule_response(
        self,
        state: ChatState,
        message: Message,
        text: str,
    ) -> None:
        """Accumulate *text* and start a new coalesced response task, cancelling any prior one."""
        state.pending_texts.append(text)

        def _on_success(t: asyncio.Task, s: ChatState = state) -> None:
            if not t.cancelled() and t.exception() is None:
                s.pending_texts.clear()

        await state.schedule_response(
            self._generate_and_send_response(message, state.combined_text, state.read_task),
            _on_success,
        )

    async def _generate_and_send_response(
        self,
        original_message: Message,
        combined_text: str,
        read_task: asyncio.Task,
    ) -> None:
        """Generate an Ollama response for the combined message text and send it."""
        try:
            reply_context = (
                original_message.reply_to_message.text
                if original_message.reply_to_message
                else None
            )
            prior_messages = await get_chat_history(original_message.chat.id, limit=20)
            history = [
                {
                    "role": "assistant" if m.sender_id is None else "user",
                    "content": m.text,
                }
                for m in prior_messages
            ]
            messages = await create_prompt(
                combined_text,
                history=history,
                reply_context=reply_context,
            )
            result = await self.ollama_manager.chat(messages=messages)
            response_text = result.get("message", {}).get("content") or None
            if response_text:
                response_text = self._postprocess_response(response_text)
                await read_task  # ensure read receipt fires before we reply
                await self._flag_typing(original_message.chat.id, response_text)
                sent = await original_message.reply_text(response_text)
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
                        "reply_to_message_id": original_message.id,
                    }
                )

        except asyncio.CancelledError:
            logger.info(
                f"Response for chat {original_message.chat.id} cancelled"
                " — superseded by a newer message"
            )
            raise
        except Exception as ex:
            logger.error(f"Error generating response: {ex}", exc_info=True)

    async def _flag_read(self, chat_id: int, max_id: int, delay: float) -> None:
        """Mark messages as read after *delay* seconds and record that the read fired."""
        await asyncio.sleep(delay)
        try:
            await self.read_chat_history(chat_id=chat_id, max_id=max_id)
        except Exception as e:
            logger.warning(f"Failed to mark chat {chat_id} as read: {e}")
        if state := self._chats.get(chat_id):
            state.read_done = True

    def _postprocess_response(self, text: str) -> str:
        """Remove empty lines and introduce a small number of human-like typos."""
        text = "\n".join(line for line in text.splitlines() if line.strip())

        # Collect positions of all eligible words (alphabetic, length >= 4).
        candidates = [(m.start(), m.group()) for m in re.finditer(r"\b[a-zA-Z]{4,}\b", text)]
        if candidates:
            # Roughly 1 typo per 40 words, at least 1, at most 3.
            typo_count = min(max(1, len(candidates) // 40), 3)
            chosen = random.sample(candidates, min(typo_count, len(candidates)))
            # Replace from right to left so earlier positions stay valid.
            chars = list(text)
            for pos, word in sorted(chosen, key=lambda x: x[0], reverse=True):
                typo = _make_typo(word)
                chars[pos : pos + len(word)] = typo
            text = "".join(chars)

        return text

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
