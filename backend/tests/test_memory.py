import json
from datetime import UTC, datetime

import pytest
from sqlalchemy import Column, Integer, Table, create_engine, inspect, select

from config import settings
from database import session
from database.memory_store import get_memory, save_memory
from database.message_store import TelegramMessage, add_message
from ollama.memory_handler import parse_facts, update_chat_memory


@pytest.fixture
async def db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    await session.init_db()
    yield tmp_path / "test.db"
    await session._engine.dispose()


class FakeOllama:
    def __init__(self, content: str):
        self.content = content
        self.calls = []

    async def chat(self, messages, **kwargs):
        self.calls.append(messages)
        return {"message": {"content": self.content}}


async def _add(chat_id: int, n: int, outgoing_every: int = 2):
    for i in range(n):
        outgoing = i % outgoing_every == 1
        await add_message(
            {
                "message_id": i,
                "chat_id": chat_id,
                "chat_type": "private",
                "sender_id": None if outgoing else 42,
                "first_name": None if outgoing else "Tom",
                "text": f"message {i}",
                "message_type": "text",
                "date": datetime.now(UTC),
            }
        )


def test_parse_facts():
    assert parse_facts('{"facts": ["- Calls You Mistress ", "", 3]}') == ["Calls You Mistress"]
    assert parse_facts("not json") is None
    assert parse_facts('{"facts": "x"}') is None


async def test_waits_for_enough_new_messages(db, monkeypatch):
    monkeypatch.setattr(settings, "MEMORY_UPDATE_EVERY", 10)
    await _add(1, 9)
    ollama = FakeOllama('{"facts": ["x"]}')
    assert not await update_chat_memory(ollama, 1, group=False)
    assert ollama.calls == []


async def test_folds_new_messages_into_facts(db, monkeypatch):
    monkeypatch.setattr(settings, "MEMORY_UPDATE_EVERY", 4)
    await _add(1, 4)
    await save_memory(1, "- Likes cats")
    ollama = FakeOllama(json.dumps({"facts": ["Likes cats", "Is called Tom"]}))

    assert await update_chat_memory(ollama, 1, group=False)
    prompt = ollama.calls[0][1]["content"]
    assert "- Likes cats" in prompt and "Them: message 0" in prompt and "You: message 1" in prompt
    memory = await get_memory(1)
    assert memory.facts == "- Likes cats\n- Is called Tom"

    # nothing new since the last update
    assert not await update_chat_memory(ollama, 1, group=False, force=True)


async def test_malformed_response_keeps_facts(db, monkeypatch):
    monkeypatch.setattr(settings, "MEMORY_UPDATE_EVERY", 1)
    await _add(1, 2)
    await save_memory(1, "- Likes cats")
    assert not await update_chat_memory(FakeOllama("oops"), 1, group=False)
    memory = await get_memory(1)
    assert (memory.facts, memory.last_message_id) == ("- Likes cats", 0)


async def test_added_table_keeps_existing_data(db):
    await _add(1, 1)
    await session._engine.dispose()

    extra = Table("zz_extra", session.Base.metadata, Column("id", Integer, primary_key=True))
    try:
        await session.init_db()
        async with session.get_db_session() as s:
            assert len((await s.execute(select(TelegramMessage))).scalars().all()) == 1
        sync_engine = create_engine(f"sqlite:///{db}")
        assert "zz_extra" in inspect(sync_engine).get_table_names()
        sync_engine.dispose()
    finally:
        session.Base.metadata.remove(extra)


async def test_media_download(db, tmp_path, monkeypatch):
    from fastapi import HTTPException

    from endpoints.memory import download_media, list_chat_media

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "photo.jpg").write_bytes(b"jpg")
    monkeypatch.setattr(settings, "TELEGRAM_MEDIA_DIR", str(media_dir))
    base = {"chat_id": 1, "chat_type": "private", "message_type": "photo", "date": datetime.now(UTC)}
    await add_message({**base, "message_id": 1, "sender_id": 42, "first_name": "Tom", "file_path": "photo.jpg"})
    await add_message({**base, "message_id": 2, "sender_id": 42, "file_path": "../test.db"})
    await add_message({**base, "message_id": 3, "sender_id": None, "file_path": "photo.jpg"})

    items = await list_chat_media(1)
    assert [(i.id, i.sender) for i in items] == [(2, None), (1, "Tom")]  # outgoing media excluded
    assert str((await download_media(1)).path) == str(media_dir / "photo.jpg")
    with pytest.raises(HTTPException):
        await download_media(2)  # outside the media directory
