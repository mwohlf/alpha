"""
Database engine, session management, and schema initialization.
"""

import logging

from config import settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

logger = logging.getLogger("alpha")

Base = declarative_base()

_engine = None
_async_session_maker = None


async def init_db() -> None:
    """Initialize the database engine and create tables."""
    global _engine, _async_session_maker

    logger.info(f"Initializing Telegram database: {settings.TELEGRAM_DATABASE_URL}")

    _engine = create_async_engine(
        settings.TELEGRAM_DATABASE_URL,
        future=True,
    )

    _async_session_maker = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Drop and recreate tables to ensure schema is always up to date
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Telegram database initialized successfully")


def get_db_session() -> AsyncSession:
    """Get a new database session."""
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _async_session_maker()
