"""Auth API routes — register, login, verify-email, refresh, profile, password."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    EmailVerifyRequest,
    ForgotPasswordRequest,
    MessageResponse,
    PasswordChange,
    RegisterPendingResponse,
    ResendVerifyRequest,
    ResetPasswordRequest,
    TokenRefresh,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
)
from app.services.user_service import UserService

router = APIRouter()


@router.post(
    "/register",
    response_model=RegisterPendingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new account. Sends a 6-digit verification code to email."""
    service = UserService(db)
    return await service.register(data)


@router.post("/verify-email", response_model=TokenResponse)
async def verify_email(data: EmailVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verify the email address with the 6-digit code. Returns JWT on success."""
    service = UserService(db)
    return await service.verify_email(data.email, data.code)


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    data: ResendVerifyRequest, db: AsyncSession = Depends(get_db)
):
    """Resend verification code (rate-limited to once per 60 s)."""
    service = UserService(db)
    await service.resend_verification(data.email)
    return MessageResponse(message="验证码已发送，请查收邮件")


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    return await service.login(data.email, data.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    return await service.refresh_token(data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.update_profile(current_user, data)


@router.put("/password", response_model=MessageResponse)
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    await service.change_password(current_user, data)
    return MessageResponse(message="密码已更新")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Send a password-reset link to the email if it exists."""
    service = UserService(db)
    await service.forgot_password(data.email)
    return MessageResponse(message="如果该邮筱已注册，重置链接已发送，请查收邮件")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password with a valid token."""
    service = UserService(db)
    await service.reset_password(data.token, data.new_password)
    return MessageResponse(message="密码重置成功，请使用新密码登录")
