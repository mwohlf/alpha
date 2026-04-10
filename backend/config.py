"""
Configuration management for the FastAPI backend.
Loads settings from environment variables with .env file support.
"""

import os
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Alpha API"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    LOGFILE: str = os.getenv("LOGFILE", "log/alpha.log")

    # Frontend
    FRONTEND_DIR: str = os.getenv("FRONTEND_DIR", "frontend/build")

    # Server
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

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
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://woodstock:11434")
    OLLAMA_DEFAULT_MODEL: str = os.getenv(
        "OLLAMA_DEFAULT_MODEL", "huihui_ai/dolphin3-abliterated:latest"
    )
    # OLLAMA_DEFAULT_MODEL: str = os.getenv("OLLAMA_DEFAULT_MODEL", "kiwi_kiwi/qwen3.5-9b-abliterated_en:latest")
    OLLAMA_ENABLED: bool = os.getenv("OLLAMA_ENABLED", "True").lower() == "true"

    # Database (when needed)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

    # Telegram Bot (pyrogram)
    TELEGRAM_API_ID: str = ""
    TELEGRAM_API_HASH: str = ""
    TELEGRAM_SESSION_NAME: str = ""
    # will be null on the first run
    TELEGRAM_SESSION_STRING: Optional[str] = None

    # Telegram Database
    TELEGRAM_DATABASE_URL: str = ""

    class Config:
        """
        we load .env with default values then override with .env.prod, or anything else if it is configured in ${ENV_FILE}
        """

        env_file = (".env", os.getenv("ENV_FILE", ".env.prod"))
        case_sensitive = True


# Global settings instance, initialized on import
settings = Settings()
