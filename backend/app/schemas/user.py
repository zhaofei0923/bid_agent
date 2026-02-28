"""User request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

# ── Request Schemas ──────────────────────────────────────────────


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)
    company: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenRefresh(BaseModel):
    refresh_token: str


class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    company: str | None = None
    avatar_url: str | None = None
    language: str | None = Field(None, pattern="^(zh|en)$")


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


# ── Response Schemas ─────────────────────────────────────────────


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    company: str | None = None
    avatar_url: str | None = None
    role: str
    language: str
    credits_balance: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class MessageResponse(BaseModel):
    message: str
