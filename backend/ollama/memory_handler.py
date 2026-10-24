"""
Keeps each chat's long-term memory: folds new messages into a short list of facts.
"""

import json
import logging

from config import settings
from database.memory_store import get_memory, save_memory
from database.message_store import TelegramMessage, get_messages_since
from ollama.ollama_client_manager import OllamaClientManager
from ollama.prompt_handler import describe_message

logger = logging.getLogger("alpha")

MEMORY_SCHEMA = {
    "type": "object",
    "properties": {"facts": {"type": "array", "items": {"type": "string"}}},
    "required": ["facts"],
}

MEMORY_SYSTEM_PROMPT = f"""You maintain the long-term memory of a chat account ("You") about the people it talks to.
You get the facts remembered so far and the newest messages. Return the complete, updated list of facts.

Keep facts that matter for future conversations:
- what they want to be called, how they address You, their stated likes, dislikes and limits
- things they told about themselves (age, hobbies, situation, mood), plans and promises
- what You demanded or ordered, whether they obeyed, tributes they claim to have sent
- recurring topics, running jokes, how the relationship has developed

Rules:
- One short, self-contained fact per item, in English, written from Your point of view ("They call You Mistress").
- In group chats, say who each fact is about.
- Keep existing facts unless the new messages contradict or update them; merge duplicates.
- Leave out small talk, greetings, and anything only relevant to the moment.
- Never record addresses, workplaces, phone numbers, email addresses, social media accounts, contacts, or payment or bank details.
- At most {settings.MEMORY_MAX_FACTS} facts, most important first. Return an empty list if nothing is worth remembering."""


def _speaker(message: TelegramMessage, group: bool) -> str:
    if message.sender_id is None:
        return "You"
    if group:
        return message.first_name or message.username or "Someone"
    return "Them"


def parse_facts(content: str) -> list[str] | None:
    """Return the facts from a structured-output response, or None if malformed."""
    try:
        facts = json.loads(content)["facts"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return None
    if not isinstance(facts, list):
        return None
    cleaned = [f.strip().lstrip("-• ").strip() for f in facts if isinstance(f, str)]
    return [f for f in cleaned if f][: settings.MEMORY_MAX_FACTS]


async def update_chat_memory(
    ollama_manager: OllamaClientManager,
    chat_id: int,
    group: bool,
    force: bool = False,
) -> bool:
    """
    Fold messages stored since the last update into the chat's facts. Without *force*,
    does nothing until MEMORY_UPDATE_EVERY new messages have arrived. Returns True if
    the memory was updated.
    """
    memory = await get_memory(chat_id)
    after_id = memory.last_message_id if memory else 0
    facts = memory.facts if memory else ""
    new_messages = await get_messages_since(chat_id, after_id, settings.MEMORY_BATCH_SIZE)
    if not new_messages or (len(new_messages) < settings.MEMORY_UPDATE_EVERY and not force):
        return False

    transcript = "\n".join(
        f"{_speaker(m, group)}: {text}"
        for m in new_messages
        if (text := describe_message(m.message_type, m.text))
    )
    messages = [
        {"role": "system", "content": MEMORY_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Facts so far:\n{facts or '(none)'}\n\nNew messages:\n{transcript}",
        },
    ]
    result = await ollama_manager.chat(messages=messages, format=MEMORY_SCHEMA, temperature=0.2)
    new_facts = parse_facts(result.get("message", {}).get("content") or "")
    if new_facts is None:
        logger.warning(f"Malformed memory update for chat {chat_id}, keeping old facts")
        return False

    await save_memory(chat_id, "\n".join(f"- {f}" for f in new_facts), new_messages[-1].id)
    logger.info(f"Updated memory for chat {chat_id}: {len(new_facts)} facts")
    return True
