"""Authentication schemas for user registration, login, profile, and JWT tokens."""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    email: str
    password: str
    name: Optional[str] = None
    full_name: Optional[str] = None


class UserRegister(UserCreate):
    pass


class UserLogin(BaseModel):
    email: str
    password: str


class UserProfile(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    role: str = "authenticated"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user: Optional[UserProfile] = None
    user_id: Optional[str] = None
    email: Optional[str] = None
