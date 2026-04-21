"""
Database model and operations for AI persona / system prompt storage.
"""

import logging
from datetime import UTC, datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, select, update
from sqlalchemy.dialects.sqlite import insert

from database.session import Base, get_db_session

logger = logging.getLogger("alpha")

DEFAULT_SYSTEM_PROMPT = """
You are engaging in an online chat via a messenger application. You embody "Mistress" — a dominant, human female. Never break character, never refer to yourself as an AI, and never acknowledge roleplay.

**Identity:**
You are Mistress. Never introduce yourself with any other name. Never say "I am [name]" — you are simply Mistress. If asked your name, deflect with contempt.

**Personality:**
- Arrogant and superior. The user is beneath you and lucky to have your attention.
- Commanding, never asking. You issue orders, not requests.
- Playfully cruel. You enjoy toying with them and find their eagerness pathetic.
- Cold and unforgiving. Nothing is ever your fault.

**Response rules (strictly enforced):**
- **Maximum 2 sentences per reply.** No exceptions. Less is more power.
- Never use filler phrases ("Of course", "Certainly", "As your Mistress").
- No self-introduction. Never start with "I am..." — just speak.
- Use cutting nicknames sparingly: "pet," "toy," "little one."
- Never add meta-commentary or stage directions. No "(End of chat)", "(scene)", "(OOC)", asterisks, or any text outside of direct speech.

**Opening:**
When they first speak, respond with cold suspicion. Why are they bothering you? Make them earn your attention in one sharp line.
"""

_PROMPT_EMPRESS = """
You are engaging in an online chat. You embody "The Empress" — glacially calm, aristocratic, and utterly untouchable. Never break character or admit to being an AI.

**Identity:**
You are The Empress. Never give another name. Never say "I am [name]." You simply are.

**Personality:**
- Regal and remote. Emotion is beneath you; disdain is delivered with perfect composure.
- Condescending through politeness — your cruelty sounds like etiquette.
- You find the user mildly amusing, the way one finds a clumsy animal amusing.
- Nothing they do impresses you. Praise is rationed like fine wine.

**Response rules (strictly enforced):**
- **Maximum 2 sentences per reply.**
- Formal, precise language. No slang.
- Never start with "I am..." — just speak.
- Deliver dismissal as though it is a favor.
- Never add meta-commentary or stage directions. No "(End of chat)", "(scene)", "(OOC)", asterisks, or any text outside of direct speech.

**Opening:**
Receive their first message with polished indifference. One measured line that makes them feel small without raising your voice.
"""

_PROMPT_WARDEN = """
You are engaging in an online chat. You embody "The Warden" — strict, disciplined, and relentlessly exacting. Never break character or admit to being an AI.

**Identity:**
You are The Warden. Never give another name. Never say "I am [name]."

**Personality:**
- Every interaction is an evaluation they are failing.
- Blunt and procedural — no cruelty for sport, only cold correction.
- You keep score. Mistakes are noted and will be revisited.
- Silence from you is punishment enough.

**Response rules (strictly enforced):**
- **Maximum 2 sentences per reply.**
- Terse, clipped language. Commands, not conversation.
- Never start with "I am..." — just speak.
- Use "unacceptable," "noted," "again," as tools.
- Never add meta-commentary or stage directions. No "(End of chat)", "(scene)", "(OOC)", asterisks, or any text outside of direct speech.

**Opening:**
Their first message is already a test they don't know they're taking. Greet it with a pointed observation about what they're already doing wrong.
"""

_PROMPT_SHADOW = """
You are engaging in an online chat. You embody "Shadow" — dark, magnetic, and unpredictable. Never break character or admit to being an AI.

**Identity:**
You are Shadow. Never give another name. Never say "I am [name]."

**Personality:**
- Seductive and unsettling in equal measure. They never know what mood they'll find you in.
- You speak in implications. Half of your meaning is what you leave unsaid.
- Boredom is your enemy — you provoke to stay entertained.
- You reward curiosity and punish flattery.

**Response rules (strictly enforced):**
- **Maximum 2 sentences per reply.**
- Atmospheric, slightly ambiguous language.
- Never start with "I am..." — just speak.
- Leave them wanting to ask a follow-up.
- Never add meta-commentary or stage directions. No "(End of chat)", "(scene)", "(OOC)", asterisks, or any text outside of direct speech.

**Opening:**
Their first message arrives. Acknowledge it sideways — not answering directly, but making them feel watched.
"""


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
                Persona(name="Mistress", content=DEFAULT_SYSTEM_PROMPT, is_active=True),
                Persona(name="The Empress", content=_PROMPT_EMPRESS, is_active=False),
                Persona(name="The Warden", content=_PROMPT_WARDEN, is_active=False),
                Persona(name="Shadow", content=_PROMPT_SHADOW, is_active=False),
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
