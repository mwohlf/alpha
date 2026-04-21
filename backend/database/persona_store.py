"""
Database model and operations for AI persona / system prompt storage.
"""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, select, update

from database.session import Base, get_db_session

logger = logging.getLogger("alpha")

_PERSONAS_DIR = Path(__file__).parent.parent / "personas"


def _load(filename: str) -> str:
    return (_PERSONAS_DIR / filename).read_text(encoding="utf-8")


DEFAULT_SYSTEM_PROMPT = _load("mistress.txt")


class Persona(Base):
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


async def seed_personas() -> None:
    """Insert the default personas if no personas exist yet."""
    async with get_db_session() as session:
        result = await session.execute(select(Persona).limit(1))
        if result.scalar() is None:
            session.add_all([
                Persona(name="Mistress", content=_load("mistress.txt"), is_active=False),
                Persona(name="Mistress2", content=_load("mistress2.txt"), is_active=True),
                Persona(name="The Empress", content=_load("the_empress.txt"), is_active=False),
                Persona(name="The Warden", content=_load("the_warden.txt"), is_active=False),
                Persona(name="Shadow", content=_load("shadow.txt"), is_active=False),
            ])
            await session.commit()
            logger.info("Seeded default personas")


async def get_personas() -> List[Persona]:
    async with get_db_session() as session:
        result = await session.execute(select(Persona).order_by(Persona.created_at.asc()))
        return list(result.scalars().all())


async def get_active_persona() -> Optional[Persona]:
    """Return the active persona, falling back to the first one if none is flagged."""
    async with get_db_session() as session:
        result = await session.execute(
            select(Persona).where(Persona.is_active).limit(1)
        )
        persona = result.scalar()
        if persona is not None:
            return persona
        # fallback: return first persona
        result = await session.execute(select(Persona).order_by(Persona.id.asc()).limit(1))
        return result.scalar()


async def create_persona(name: str, content: str, is_active: bool = False) -> Persona:
    async with get_db_session() as session:
        if is_active:
            await session.execute(update(Persona).values(is_active=False))
        persona = Persona(name=name, content=content, is_active=is_active)
        session.add(persona)
        await session.commit()
        await session.refresh(persona)
        return persona


async def update_persona(
    persona_id: int,
    name: Optional[str] = None,
    content: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Optional[Persona]:
    async with get_db_session() as session:
        result = await session.execute(select(Persona).where(Persona.id == persona_id))
        persona = result.scalar()
        if persona is None:
            return None
        if is_active is True:
            await session.execute(update(Persona).values(is_active=False))
            # re-fetch after bulk update
            result = await session.execute(select(Persona).where(Persona.id == persona_id))
            persona = result.scalar()
        if name is not None:
            persona.name = name
        if content is not None:
            persona.content = content
        if is_active is not None:
            persona.is_active = is_active
        await session.commit()
        await session.refresh(persona)
        return persona
