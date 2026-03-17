"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for user creation"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response (excludes password)"""
    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    created_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
