"""
Database engine, session management, and schema initialization.
"""

import hashlib
import logging

from sqlalchemy import Column, Integer, MetaData, String, delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from config import settings

logger = logging.getLogger("alpha")

Base = declarative_base()

_engine = None
_async_session_maker = None


class SchemaVersion(Base):
    """Single-row table holding the fingerprint of the schema the database was created with."""

    __tablename__ = "schema_version"

    id = Column(Integer, primary_key=True)
    fingerprint = Column(String(64), nullable=False)


def _schema_fingerprint(only: set[str] | None = None) -> str:
    """Hash of all tables (or just the tables named in *only*), columns and indexes defined in the models."""
    parts = []
    tables = [t for t in Base.metadata.tables.values() if only is None or t.name in only]
    for table in sorted(tables, key=lambda t: t.name):
        parts.append(f"table {table.name}")
        for col in table.columns:
            parts.append(f"  col {col.name} {col.type} null={col.nullable} pk={col.primary_key}")
        for idx in sorted(table.indexes, key=lambda i: i.name or ""):
            parts.append(f"  idx {idx.name} {[c.name for c in idx.columns]} unique={idx.unique}")
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def _sync_schema(conn) -> bool:
    """
    Create the schema, or drop and recreate everything if the models changed since the
    database was created. Tables that were only added are created without touching the
    existing ones. Returns True if existing data was discarded.
    """
    fingerprint = _schema_fingerprint()
    existing = MetaData()
    existing.reflect(bind=conn)

    stored = None
    if SchemaVersion.__tablename__ in existing.tables:
        stored = conn.execute(select(SchemaVersion.fingerprint)).scalar()

    if existing.tables and stored != fingerprint and stored == _schema_fingerprint(set(existing.tables)):
        # existing tables are unchanged, the models only gained new tables
        Base.metadata.create_all(bind=conn)
        conn.execute(SchemaVersion.__table__.update().values(fingerprint=fingerprint))
        return False

    reset = bool(existing.tables) and stored != fingerprint
    if reset:
        # drop every table present in the database, including ones no longer in the models
        existing.drop_all(bind=conn)
    if reset or not existing.tables:
        Base.metadata.create_all(bind=conn)
        conn.execute(SchemaVersion.__table__.insert().values(id=1, fingerprint=fingerprint))
    return reset


async def init_db() -> None:
    """Initialize the database engine and create tables, resetting them on schema changes."""
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

    async with _engine.begin() as conn:
        if await conn.run_sync(_sync_schema):
            logger.warning("Database schema changed — existing data was discarded")

    logger.info("Telegram database initialized successfully")


async def wipe_db() -> dict[str, int]:
    """Delete all rows from every table (the schema is kept). Returns rows deleted per table."""
    deleted = {}
    async with get_db_session() as session:
        for table in reversed(Base.metadata.sorted_tables):
            if table.name == SchemaVersion.__tablename__:
                continue
            result = await session.execute(delete(table))
            deleted[table.name] = result.rowcount
        await session.commit()
    logger.info(f"Database wiped: {deleted}")
    return deleted


def get_db_session() -> AsyncSession:
    """Get a new database session."""
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _async_session_maker()
