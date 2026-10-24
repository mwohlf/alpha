import pytest

from config import settings
from database import persona_store, session
from database.persona_store import create_persona, get_personas, sync_personas, update_persona


@pytest.fixture
async def personas_dir(tmp_path, monkeypatch):
    """Empty personas directory and a fresh SQLite database per test."""
    directory = tmp_path / "personas"
    directory.mkdir()
    monkeypatch.setattr(persona_store, "_PERSONAS_DIR", directory)
    monkeypatch.setattr(settings, "TELEGRAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    await session.init_db()
    yield directory
    await session._engine.dispose()


def _write(directory, **files):
    for stem, content in files.items():
        (directory / f"{stem}.txt").write_text(content, encoding="utf-8")


async def _state():
    return {p.name: (p.content, p.is_active) for p in await get_personas()}


async def test_creates_personas_from_files_and_activates_default(personas_dir):
    _write(personas_dir, character1="one", character2="two")
    await sync_personas()
    assert await _state() == {"Character1": ("one", False), "Character2": ("two", True)}


async def test_new_file_is_added_on_next_sync(personas_dir):
    _write(personas_dir, character1="one", character2="two")
    await sync_personas()
    _write(personas_dir, character6="six")
    await sync_personas()
    assert (await _state())["Character6"] == ("six", False)


async def test_directory_overrides_database_and_keeps_active(personas_dir):
    _write(personas_dir, character1="one", character2="two")
    await sync_personas()
    one = next(p for p in await get_personas() if p.name == "Character1")
    await update_persona(one.id, content="edited", is_active=True)
    await create_persona("Custom", "custom")

    await sync_personas()
    assert await _state() == {"Character1": ("one", True), "Character2": ("two", False)}


async def test_falls_back_to_first_persona_when_active_file_removed(personas_dir):
    _write(personas_dir, character2="two", character3="three", character4="four")
    await sync_personas()
    (personas_dir / "character2.txt").unlink()
    await sync_personas()
    assert await _state() == {"Character3": ("three", True), "Character4": ("four", False)}
