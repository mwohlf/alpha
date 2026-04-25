"""
Builds ChatML message lists for Ollama requests.
"""

import logging
from typing import TypedDict

from database.persona_store import get_active_persona

logger = logging.getLogger("alpha")


class ChatMessage(TypedDict):
    role: str
    content: str


async def create_prompt(
    text: str,
    history: list[ChatMessage] | None = None,
    reply_context: str | None = None,
) -> list[ChatMessage]:
    """
    Build a ChatML message list from the active persona, history, and user text.

    Returns messages for the caller to pass directly to ollama_manager.chat().

    Roles used:
      - system   : active persona / instructions
      - user     : messages from the remote user
      - assistant: prior responses from the bot
    """
    persona = await get_active_persona()
    messages: list[ChatMessage] = [{"role": "system", "content": persona.content}]

    if history:
        messages.extend(history)

    if reply_context:
        user_content = f"[Replying to: {reply_context}]\n\n{text}"
    else:
        user_content = text

    messages.append({"role": "user", "content": user_content})

    logger.info(f"Built prompt for message: {text[:50]}...")

    return messages
