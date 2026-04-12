"""
Configuration management for the FastAPI backend.
Loads settings from environment variables with .env file support.
"""

from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Alpha"
    ENVIRONMENT: str = "dev"
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

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_set(cls, v: str) -> str:
        if not v:
            raise ValueError("SECRET_KEY must be set in the environment or .env file")
        return v

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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance, initialized on import
settings = Settings()
