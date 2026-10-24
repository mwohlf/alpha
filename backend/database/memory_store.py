"""
Database model and operations for long-term per-chat memory.
"""

import logging
from datetime import UTC, datetime
from typing import List, Optional

from sqlalchemy import BigInteger, Column, DateTime, Integer, Text, select

from database.session import Base, get_db_session

logger = logging.getLogger("alpha")


class ChatMemory(Base):
    """Important facts about a chat, one per line, kept across conversations."""

    __tablename__ = "chat_memories"

    chat_id = Column(BigInteger, primary_key=True)
    facts = Column(Text, nullable=False, default="")
    # TelegramMessage.id of the newest message already folded into the facts
    last_message_id = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))


async def get_memory(chat_id: int) -> Optional[ChatMemory]:
    async with get_db_session() as session:
        return await session.get(ChatMemory, chat_id)


async def get_memories() -> List[ChatMemory]:
    async with get_db_session() as session:
        result = await session.execute(select(ChatMemory))
        return list(result.scalars().all())


async def save_memory(chat_id: int, facts: str, last_message_id: Optional[int] = None) -> ChatMemory:
    """Create or replace a chat's facts; *last_message_id* is kept unless given."""
    async with get_db_session() as session:
        memory = await session.get(ChatMemory, chat_id)
        if memory is None:
            memory = ChatMemory(chat_id=chat_id, last_message_id=0)
            session.add(memory)
        memory.facts = facts
        if last_message_id is not None:
            memory.last_message_id = last_message_id
        memory.updated_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(memory)
        logger.info(f"Saved memory for chat {chat_id}")
        return memory

