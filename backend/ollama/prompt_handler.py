"""
Builds ChatML message lists for Ollama requests.
"""

import json
import logging
import re
from typing import TypedDict

from database.persona_store import get_active_persona

logger = logging.getLogger("alpha")

# Structured output: Ollama constrains the response to this schema. "notes" comes first
# and gives the model a place for narration, tone or out-of-character remarks, so they
# stay out of "reply"; notes are only logged, never sent.
REPLY_SCHEMA = {
    "type": "object",
    "properties": {
        "notes": {"type": "string"},
        "reply": {"type": "string"},
    },
    "required": ["notes", "reply"],
}

REPLY_FORMAT_INSTRUCTION = (
    'Respond with JSON of the form {"notes": "...", "reply": "..."}. '
    "Put anything that is not part of your chat message into notes: actions, tone, "
    "narration, scene descriptions, out-of-character remarks, plans. Notes are never "
    "shown to anyone. The reply field holds only the exact words you type into the "
    "chat — if a sentence would not be typed by you in a text message, it belongs in "
    "notes. notes may be empty."
)

GROUP_CHAT_INSTRUCTION = (
    "This is a group chat. Each message from the others starts with the sender's name "
    'and a colon, e.g. "Alex: hi". Do not start your own reply with a name.'
)

# Persona example lines: - User says "hello" -> you reply "Introduce yourself."
_EXAMPLE_LINE = re.compile(r'^- User says "(.*)" -> you reply "(.*)"\s*$', re.MULTILINE)
_EXAMPLES_HEADER = re.compile(r"^Examples?:\s*$", re.MULTILINE)


# Media the model is told about; it cannot see the content, only that something arrived.
# Locations and contacts are deliberately left out.
_MEDIA_LABELS = {
    "photo": "a photo",
    "video": "a video",
    "animation": "a GIF",
    "sticker": "a sticker",
    "voice": "a voice message",
    "audio": "an audio file",
    "document": "a file",
}


def describe_message(message_type: str, text: str | None) -> str | None:
    """Text of a message for the model; media becomes e.g. "(sent a photo) caption"."""
    label = _MEDIA_LABELS.get(message_type)
    if label is None:
        return text
    return f"(sent {label}) {text}" if text else f"(sent {label})"


class ChatMessage(TypedDict):
    role: str
    content: str


def split_examples(persona: str) -> tuple[str, list[ChatMessage]]:
    """
    Move the persona's example exchanges out of the system prompt into user/assistant
    turns — small models imitate real turns far more reliably than described ones.
    """
    examples: list[ChatMessage] = []
    for user_text, reply in _EXAMPLE_LINE.findall(persona):
        examples.append({"role": "user", "content": user_text})
        examples.append({"role": "assistant", "content": reply})
    if not examples:
        return persona, []
    system = _EXAMPLES_HEADER.sub("", _EXAMPLE_LINE.sub("", persona))
    return re.sub(r"\n{3,}", "\n\n", system).strip(), examples


def parse_reply(content: str) -> str:
    """Return the reply text from a structured-output response ("" if malformed)."""
    try:
        data = json.loads(content)
        reply = data.get("reply", "")
    except (json.JSONDecodeError, AttributeError):
        logger.warning(f"Malformed structured reply: {content[:200]}")
        return ""
    if notes := data.get("notes"):
        logger.info(f"Discarded model notes: {notes}")
    return reply.strip() if isinstance(reply, str) else ""


async def create_prompt(
    text: str,
    history: list[ChatMessage] | None = None,
    reply_context: str | None = None,
    json_reply: bool = False,
    memory: str | None = None,
    group_chat: bool = False,
) -> list[ChatMessage]:
    """
    Build a ChatML message list from the active persona, history, and user text.

    Returns messages for the caller to pass directly to ollama_manager.chat().
    With *json_reply*, the system prompt asks for REPLY_SCHEMA; pass it as
    ``format`` and read the answer with parse_reply(). *memory* holds the chat's
    long-term facts; with *group_chat*, user messages are expected to carry the
    sender's name.

    Roles used:
      - system   : active persona / instructions
      - user     : messages from the remote user (and persona examples)
      - assistant: prior responses from the bot (and persona examples)
    """
    persona = await get_active_persona()
    system, examples = split_examples(persona.content)
    if memory:
        system = (
            f"{system}\n\nWhat you remember from earlier conversations in this chat "
            f"(use it naturally, never recite it):\n{memory}"
        )
    if group_chat:
        system = f"{system}\n\n{GROUP_CHAT_INSTRUCTION}"
    if json_reply:
        system = f"{system}\n\n{REPLY_FORMAT_INSTRUCTION}"
    messages: list[ChatMessage] = [{"role": "system", "content": system}]
    messages.extend(examples)

    if history:
        messages.extend(history)

    if reply_context:
        user_content = f"(replying to: {reply_context})\n\n{text}"
    else:
        user_content = text

    messages.append({"role": "user", "content": user_content})

    logger.info(f"Built prompt for message: {text[:50]}...")
    logger.info(f"Complete generated messages: {messages}")

    return messages
