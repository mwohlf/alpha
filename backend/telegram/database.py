"""
Database models and operations for Telegram message storage.
"""

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import BigInteger, Column, DateTime, Index, Integer, String, Text, select, delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from config import settings

logger = logging.getLogger("uvicorn.error")

Base = declarative_base()


class TelegramMessage(Base):
    """SQLAlchemy model for storing Telegram messages."""

    __tablename__ = "telegram_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(BigInteger, nullable=False)
    chat_id = Column(BigInteger, nullable=False)
    chat_title = Column(String(255), nullable=True)
    chat_type = Column(String(50), nullable=False)
    user_id = Column(BigInteger, nullable=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    text = Column(Text, nullable=True)
    message_type = Column(String(50), nullable=False)
    date = Column(DateTime, nullable=False)
    reply_to_message_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes for common queries
    __table_args__ = (
        Index("idx_chat_id", "chat_id"),
        Index("idx_date", "date"),
        Index("idx_user_id", "user_id"),
    )


# Global async engine and session maker
_engine = None
_async_session_maker = None


async def init_db() -> None:
    """Initialize the database engine and create tables."""
    global _engine, _async_session_maker

    logger.info(f"Initializing Telegram database: {settings.TELEGRAM_DATABASE_URL}")

    _engine = create_async_engine(
        settings.TELEGRAM_DATABASE_URL,
        echo=settings.DEBUG,
        future=True,
    )

    _async_session_maker = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create tables
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Telegram database initialized successfully")


def get_db_session() -> AsyncSession:
    """Get a new database session."""
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _async_session_maker()


async def add_message(message_data: dict) -> None:
    """
    Add a message to the database.

    Args:
        message_data: Dictionary containing message information
    """
    async with get_db_session() as session:
        try:
            message = TelegramMessage(**message_data)
            session.add(message)
            await session.commit()
            logger.debug(f"Stored message {message_data['message_id']} from chat {message_data['chat_id']}")
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to store message: {e}", exc_info=True)
            raise


async def get_recent_messages(
    limit: int = 100,
    chat_id: Optional[int] = None
) -> List[TelegramMessage]:
    """
    Get recent messages from the database.

    Args:
        limit: Maximum number of messages to return
        chat_id: Optional filter by chat ID

    Returns:
        List of TelegramMessage objects
    """
    async with get_db_session() as session:
        try:
            query = select(TelegramMessage).order_by(TelegramMessage.date.desc()).limit(limit)

            if chat_id is not None:
                query = query.where(TelegramMessage.chat_id == chat_id)

            result = await session.execute(query)
            messages = result.scalars().all()
            return list(messages)
        except Exception as e:
            logger.error(f"Failed to query messages: {e}", exc_info=True)
            raise


async def get_message_count() -> int:
    """
    Get the total count of stored messages.

    Returns:
        Number of messages in database
    """
    async with get_db_session() as session:
        try:
            result = await session.execute(select(TelegramMessage))
            messages = result.scalars().all()
            return len(messages)
        except Exception as e:
            logger.error(f"Failed to count messages: {e}", exc_info=True)
            return 0


async def clear_messages() -> int:
    """
    Clear all messages from the database.

    Returns:
        Number of messages deleted
    """
    async with get_db_session() as session:
        try:
            # Get count before deleting
            result = await session.execute(select(TelegramMessage))
            count = len(result.scalars().all())

            # Delete all messages
            await session.execute(delete(TelegramMessage))
            await session.commit()

            logger.info(f"Cleared {count} messages from database")
            return count
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to clear messages: {e}", exc_info=True)
            raise
