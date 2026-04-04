"""
Pydantic models for Telegram API responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


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
