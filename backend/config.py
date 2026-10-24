"""
Configuration management for the FastAPI backend.
Loads settings from environment variables with .env file support.
"""

import os
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings

# Env files are resolved relative to the workspace root so they load regardless of cwd.
# ENV_FILE (e.g. ".env.dev") overrides values from .env; real env vars override both.
_ROOT_DIR = Path(__file__).resolve().parent.parent
_ENV_FILES = tuple(
    _ROOT_DIR / name for name in (".env", os.environ.get("ENV_FILE")) if name
)


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Alpha"
    APP_API_NAME: str = "Alpha API"  # this is backed into the OpenAPI generated code
    DEBUG: bool = True
    LOGFILE: str = "log/alpha.log"

    # Frontend
    FRONTEND_DIR: str = "frontend/dist"

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Security
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    LOGIN_USERNAME: str = "admin"
    LOGIN_PASSWORD: str = "admin"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Ollama
    OLLAMA_BASE_URL: str = "http://woodstock:11434"
    OLLAMA_DEFAULT_MODEL: str = "huihui_ai/dolphin3-abliterated:latest"
    # OLLAMA_DEFAULT_MODEL: str = "kiwi_kiwi/qwen3.5-9b-abliterated_en:latest"
    OLLAMA_ENABLED: bool = True
    # retry interval when Ollama is unreachable at startup
    OLLAMA_RETRY_SECONDS: int = 30

    # Database (when needed)
    DATABASE_URL: str = "sqlite:///./app.db"

    # Telegram Bot (pyrogram)
    TELEGRAM_API_ID: str = ""
    TELEGRAM_API_HASH: str = ""
    TELEGRAM_SESSION_NAME: str = ""
    # will be null on the first run
    TELEGRAM_SESSION_STRING: Optional[str] = None

    # Telegram Database
    TELEGRAM_DATABASE_URL: str = ""

    # Telegram Media: received photos/videos/...; inside etc/ so the Docker volume keeps them
    TELEGRAM_MEDIA_DIR: str = "etc/media"

    # Long-term memory: refresh a chat's facts once this many new messages arrived
    MEMORY_UPDATE_EVERY: int = 10
    # most messages folded into the facts per refresh (older backlog is caught up later)
    MEMORY_BATCH_SIZE: int = 60
    MEMORY_MAX_FACTS: int = 25

    @property
    def media_path(self) -> Path:
        """Absolute media directory (relative values are resolved from the working directory)."""
        return Path(self.TELEGRAM_MEDIA_DIR).resolve()

    class Config:
        env_file = _ENV_FILES
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance, initialized on import
settings = Settings()
