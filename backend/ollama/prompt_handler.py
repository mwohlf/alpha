"""
Bridge between the Telegram client and Ollama for AI-powered message responses.
"""

import logging
from typing import Optional

from database.persona_store import DEFAULT_SYSTEM_PROMPT, get_active_persona

logger = logging.getLogger("alpha")


# maybe move this into the ollama client manager itself?


async def create_prompt(
    ollama_manager,
    text: str,
    history: Optional[list] = None,
    reply_context: Optional[str] = None,
) -> Optional[str]:
    """
    this creates the prompt in JSON format following the ChatML standard
    we may use
      - system
      - user
      - assistant
      - developer

    """
    try:
        persona = await get_active_persona()
        system_prompt = persona.content if persona else DEFAULT_SYSTEM_PROMPT
        messages = [{"role": "system", "content": system_prompt}]

        if history:
            messages.extend(history)

        if reply_context:
            messages.append(
                {"role": "user", "content": f"[Previous message]: {reply_context}"}
            )

        messages.append({"role": "user", "content": text})

        logger.info(f"Processing message with Ollama: {text[:50]}...")

        response = await ollama_manager.chat(messages=messages)
        return response.get("message", {}).get("content") or None

    except Exception as e:
        logger.error(f"Error processing message with Ollama: {e}", exc_info=True)
        return None
