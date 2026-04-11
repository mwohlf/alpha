from fastapi import HTTPException, Request, status
from ollama.ollama_client import OllamaClientManager
from telegram.client_manager import TelegramClientManager


def get_telegram_manager(request: Request) -> TelegramClientManager:
    manager = getattr(request.app.state, "telegram_manager", None)
    if not manager:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram client not initialized.")
    return manager


def get_ollama_manager(request: Request) -> OllamaClientManager:
    manager = getattr(request.app.state, "ollama_manager", None)
    if not manager:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Ollama client not initialized.")
    return manager


