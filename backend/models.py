from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Model(BaseModel):
    """Represents a specific AI model configuration."""

    unique_id: str = Field(
        ...,
        alias="uniqueId",  # Maps camelCase from JSON to snake_case in Python
        examples=["llama3:latest"],
        description="The unique identifier for the model",
    )
    description: str = Field(..., examples=["Meta Llama 3 8B model"], description="A brief description of the model capabilities")

    class Config:
        # This allows the API to accept 'uniqueId' but let you use 'unique_id' in Python
        populate_by_name = True


class ModelListGetResponse(BaseModel):
    """Response containing a collection of available models."""

    models: list[Model] = Field(default_factory=list, description="A list of available AI models")


class HealthGetResponse(BaseModel):
    status: Optional[str] = Field(None, examples=["healthy"])


class HelloGetResponse(BaseModel):
    message: str = Field(..., examples=["Hello from FastAPI"])


class ProtectedGetResponse(BaseModel):
    message: Optional[str] = Field(None, examples=["This is a protected endpoint"])


class ProtectedGetResponse401(BaseModel):
    detail: Optional[str] = Field(None, examples=["Invalid authentication credentials"])


class TelegramUserInfo(BaseModel):
    """User information from a Telegram message."""

    user_id: Optional[int] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class TelegramChatInfo(BaseModel):
    """Chat information from a Telegram message."""

    chat_id: int
    chat_type: str
    title: Optional[str] = None


class TelegramMessageResponse(BaseModel):
    """Response model for a Telegram message."""

    id: int
    message_id: int
    chat: TelegramChatInfo
    user: Optional[TelegramUserInfo] = None
    text: Optional[str] = None
    message_type: str
    date: datetime
    reply_to_message_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TelegramStatusResponse(BaseModel):
    """Response model for Telegram client status."""

    connected: bool
    user_id: Optional[int] = None
    username: Optional[str] = None
    message_count: int


class TelegramClearResponse(BaseModel):
    """Response model for clearing messages."""

    success: bool
    messages_deleted: int


ModelListGetResponse.model_rebuild()
