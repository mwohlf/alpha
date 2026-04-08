from typing import List, Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from ollama.ollama_client import OllamaClientManager

from config import settings
from models import (
    HealthGetResponse,
    HelloGetResponse,
    Model,
    ModelListGetResponse,
    ProtectedGetResponse,
    TelegramChatInfo,
    TelegramClearResponse,
    TelegramMessageResponse,
    TelegramStatusResponse,
    TelegramUserInfo,
)
from telegram.message_store import clear_messages, get_message_count, get_recent_messages

router = APIRouter()

# Security
security = HTTPBearer()


def get_telegram_manager(request: Request):
    manager = getattr(request.app.state, "telegram_manager", None)
    if not manager:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram client not initialized.")
    return manager


def get_ollama_manager(request: Request) -> OllamaClientManager:
    manager = getattr(request.app.state, "ollama_manager", None)
    if not manager:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Ollama client not initialized.")
    return manager


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token from Authorization header"""
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============== Generated Endpoints ==============


# this is probably for Kubernetes
@router.get("/health", summary="Health check endpoint", tags=[], response_model=HealthGetResponse, operation_id="get_health")
def get_health() -> HealthGetResponse:
    """
    Health check endpoint
    """
    return HealthGetResponse(status="healthy")


# testing
@router.get("/hello", summary="Returns a hello message", tags=[], response_model=HelloGetResponse, operation_id="get_hello")
def get_hello() -> HelloGetResponse:
    """
    Returns a hello message
    """
    return HelloGetResponse(message="Hello from FastAPI")


@router.get("/model/list", summary="Get all models", response_model=ModelListGetResponse, operation_id="get_model_list")
def get_model_list(ollamaManager=Depends(get_ollama_manager)):
    """
    Returns a list of all available models.
    """
    # Example logic: replace with your actual database/state call
    return ModelListGetResponse(models=[Model(uniqueId="llama3", description="Meta Llama 3")])


@router.delete("/model/delete/{id}", summary="Delete a model", response_model=HelloGetResponse, operation_id="delete_model")
def delete_model(id: str, ollamaManager=Depends(get_ollama_manager)):
    """
    Deletes a specific model by ID.
    """
    # ollamaManager.
    return None


@router.post("/model/add", summary="Download and add a new model", response_model=Model, operation_id="add_model")
def add_model(unique_id: str, ollamaManager=Depends(get_ollama_manager)):
    """
    Adds a new model configuration.
    """
    # Logic to save model...
    model = {unique_id: unique_id}
    return model


# =================================


@router.get(
    "/protected",
    summary="Protected endpoint requiring JWT token",
    tags=[],
    response_model=ProtectedGetResponse,
    operation_id="get_protected",
    dependencies=[Depends(verify_token)],
)
def get_protected() -> ProtectedGetResponse:
    """
    Protected endpoint requiring JWT token
    """
    return ProtectedGetResponse(message="This is a protected endpoint")


# telegram, work in progress


@router.get(
    "/telegram/status",
    summary="Get Telegram client status",
    tags=["telegram"],
    response_model=TelegramStatusResponse,
    operation_id="get_telegram_status",
    dependencies=[Depends(verify_token)],
)
async def get_telegram_status(request: Request) -> TelegramStatusResponse:
    """
    Get Telegram client connection status and message count.
    Requires JWT authentication.
    """
    telegram_manager = getattr(request.app.state, "telegram_manager", None)

    if not telegram_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram client not initialized. Check TELEGRAM_API_ID and TELEGRAM_API_HASH configuration.",
        )

    connected = telegram_manager.is_running()
    user_id = telegram_manager.get_user_id()
    username = telegram_manager.get_username()
    message_count = await get_message_count()

    return TelegramStatusResponse(connected=connected, user_id=user_id, username=username, message_count=message_count)


@router.get(
    "/telegram/messages",
    summary="Get recent Telegram messages",
    tags=["telegram"],
    response_model=List[TelegramMessageResponse],
    operation_id="get_telegram_messages",
    dependencies=[Depends(verify_token)],
)
async def get_telegram_messages(
    request: Request,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of messages to return"),
    chat_id: Optional[int] = Query(None, description="Filter by chat ID"),
) -> List[TelegramMessageResponse]:
    """
    Get recent Telegram messages from the database.
    Requires JWT authentication.

    Args:
        limit: Maximum number of messages to return (1-1000, default 100)
        chat_id: Optional filter by chat ID
    """
    telegram_manager = getattr(request.app.state, "telegram_manager", None)

    if not telegram_manager:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram client not initialized.")

    try:
        messages = await get_recent_messages(limit=limit, chat_id=chat_id)

        # Convert SQLAlchemy models to Pydantic response models
        response = []
        for msg in messages:
            response.append(
                TelegramMessageResponse(
                    id=msg.id,
                    message_id=msg.message_id,
                    chat=TelegramChatInfo(chat_id=msg.chat_id, chat_type=msg.chat_type, title=msg.chat_title),
                    user=TelegramUserInfo(user_id=msg.user_id, username=msg.username, first_name=msg.first_name, last_name=msg.last_name)
                    if msg.user_id
                    else None,
                    text=msg.text,
                    message_type=msg.message_type,
                    date=msg.date,
                    reply_to_message_id=msg.reply_to_message_id,
                    created_at=msg.created_at,
                )
            )

        return response

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve messages: {str(e)}")


@router.delete(
    "/telegram/messages",
    summary="Clear all Telegram messages",
    tags=["telegram"],
    response_model=TelegramClearResponse,
    operation_id="clear_telegram_messages",
    dependencies=[Depends(verify_token)],
)
async def clear_telegram_messages(request: Request) -> TelegramClearResponse:
    """
    Clear all stored Telegram messages from the database.
    Requires JWT authentication.
    """
    telegram_manager = getattr(request.app.state, "telegram_manager", None)

    if not telegram_manager:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram client not initialized.")

    try:
        deleted_count = await clear_messages()
        return TelegramClearResponse(success=True, messages_deleted=deleted_count)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to clear messages: {str(e)}")
