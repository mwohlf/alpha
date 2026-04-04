"""
Configuration management for the FastAPI backend.
Loads settings from environment variables with .env file support.
"""

import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Alpha API"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    # Frontend
    FRONTEND_DIR: str = os.getenv("FRONTEND_DIR", "frontend/dist")


    # Server
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Ollama
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://woodstock:11434")
    OLLAMA_DEFAULT_MODEL: str = os.getenv("OLLAMA_DEFAULT_MODEL", "huihui_ai/dolphin3-abliterated:latest")
    # OLLAMA_DEFAULT_MODEL: str = os.getenv("OLLAMA_DEFAULT_MODEL", "kiwi_kiwi/qwen3.5-9b-abliterated_en:latest")
    OLLAMA_ENABLED: bool = os.getenv("OLLAMA_ENABLED", "True").lower() == "true"


    # Database (when needed)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

    # Telegram Bot (Pyrogram)
    TELEGRAM_API_ID: str
    TELEGRAM_API_HASH: str
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
    TELEGRAM_PHONE_NUMBER: str = os.getenv("TELEGRAM_PHONE_NUMBER", "")

    # Telegram Session
    TELEGRAM_SESSION_DIR: str = os.getenv("TELEGRAM_SESSION_DIR", "backend/.telegram_sessions")
    TELEGRAM_SESSION_NAME: str = os.getenv("TELEGRAM_SESSION_NAME", "alpha_userbot")

    # Telegram Database
    TELEGRAM_DATABASE_URL: str = os.getenv(
        "TELEGRAM_DATABASE_URL",
        "sqlite+aiosqlite:///backend/telegram_messages.db"
    )

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
