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


class EmailVerifyRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class ResendVerifyRequest(BaseModel):
    email: EmailStr


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
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RegisterPendingResponse(BaseModel):
    """Returned when registration succeeds but email verification is required."""

    need_verify: bool = True
    email: str
    message: str = "注册成功，请查收验证邮件并输入验证码"


class MessageResponse(BaseModel):
    message: str
