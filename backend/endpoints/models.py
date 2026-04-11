from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HealthGetResponse(BaseModel):
    status: Optional[str] = Field(None, examples=["healthy"])


class ModelDetails(BaseModel):
    """Details about an Ollama model's format and family."""

    format: Optional[str] = None
    family: Optional[str] = None
    families: Optional[list[str]] = None
    parameter_size: Optional[str] = None
    quantization_level: Optional[str] = None


class OllamaModel(BaseModel):
    """A locally available Ollama model."""

    name: str
    model: Optional[str] = None
    modified_at: Optional[str] = None
    size: Optional[int] = None
    digest: Optional[str] = None
    details: Optional[ModelDetails] = None


class ModelListGetResponse(BaseModel):
    """Response containing a collection of available models."""

    models: list[OllamaModel] = Field(default_factory=list)


class ModelDeleteResponse(BaseModel):
    deleted: str


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
    sender_id: Optional[int] = None
    receiver_id: Optional[int] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
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


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TelegramUserSummary(BaseModel):
    """A distinct sender seen in stored Telegram messages."""

    sender_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    message_count: int


class ChatMessage(BaseModel):
    """A single message in a chat conversation."""

    role: str = Field(..., examples=["user"], description="Either 'user' or 'assistant'")
    content: str = Field(..., examples=["Hello!"])


class ChatRequest(BaseModel):
    """Request to send a message to the Ollama backend."""

    message: str = Field(..., examples=["What is the meaning of life?"])
    history: list[ChatMessage] = Field(default_factory=list, description="Prior conversation turns")


class ChatResponse(BaseModel):
    """Response from the Ollama backend."""

    reply: str = Field(..., examples=["42."])


