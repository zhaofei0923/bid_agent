"""User service — registration, authentication, profile management."""

import logging
from uuid import UUID

import secrets

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.email import (
    generate_verify_code,
    pwd_reset_key,
    pwd_reset_rate_key,
    send_reset_password_email,
    send_verification_email,
    verify_code_key,
    verify_rate_key,
)
from app.core.exceptions import AuthenticationError, NotFoundError, ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.user import (
    PasswordChange,
    RegisterPendingResponse,
    TokenResponse,
    UserRegister,
    UserUpdate,
)

logger = logging.getLogger(__name__)


def _get_redis() -> aioredis.Redis:
    return aioredis.from_url(settings.REDIS_URL, decode_responses=True)


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User", str(user_id))
        return user

    # ── Registration ─────────────────────────────────────────────

    async def register(self, data: UserRegister) -> RegisterPendingResponse:
        """Create user (unverified) and send email verification code."""
        existing = await self.get_by_email(data.email)
        if existing:
            if existing.is_verified:
                raise ValidationError("该邮箱已注册，请直接登录")
            # Unverified duplicate → resend code
            await self._send_code(data.email, existing.name)
            return RegisterPendingResponse(email=data.email)

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            name=data.name,
            company=data.company,
            is_verified=False,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        await self._send_code(data.email, data.name)
        return RegisterPendingResponse(email=data.email)

    async def _send_code(self, email: str, name: str = "") -> None:
        """Generate & store verification code in Redis, then send email."""
        r = _get_redis()
        try:
            # Rate limiting
            rate_key = verify_rate_key(email)
            if await r.exists(rate_key):
                ttl = await r.ttl(rate_key)
                raise ValidationError(f"发送太频繁，请 {ttl} 秒后再试")

            code = generate_verify_code()
            code_key = verify_code_key(email)
            await r.setex(code_key, settings.VERIFY_CODE_TTL, code)
            await r.setex(rate_key, settings.VERIFY_CODE_RATE_LIMIT, "1")

            await send_verification_email(email, code, name)
            logger.info("Verification code sent for %s", email)
        finally:
            await r.aclose()

    async def verify_email(self, email: str, code: str) -> TokenResponse:
        """Verify email code and return JWT tokens on success."""
        r = _get_redis()
        try:
            stored = await r.get(verify_code_key(email))
            if not stored:
                raise ValidationError("验证码已过期，请重新发送")
            if stored != code:
                raise ValidationError("验证码不正确")

            user = await self.get_by_email(email)
            if not user:
                raise NotFoundError("User", email)

            user.is_verified = True
            await self.db.commit()
            await self.db.refresh(user)

            # Clean up code from Redis
            await r.delete(verify_code_key(email))
        finally:
            await r.aclose()

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def resend_verification(self, email: str) -> None:
        """Resend verification code to a registered-but-unverified email."""
        user = await self.get_by_email(email)
        if not user:
            # Don't leak whether email exists; silently succeed
            logger.info("Resend requested for unknown email %s (ignored)", email)
            return
        if user.is_verified:
            raise ValidationError("该邮箱已完成验证")
        await self._send_code(email, user.name)

    # ── Login ────────────────────────────────────────────────────

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("邮箱或密码不正确")

        if not user.is_verified:
            raise ValidationError("邮箱尚未验证，请先完成邮箱验证")

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh_token(self, refresh_token_str: str) -> TokenResponse:
        payload = decode_token(refresh_token_str)
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid refresh token")

        user_id = payload.get("sub")
        user = await self.get_by_id(UUID(user_id))

        access_token = create_access_token(str(user.id))
        new_refresh = create_refresh_token(str(user.id))
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ── Profile ──────────────────────────────────────────────────

    async def update_profile(self, user: User, data: UserUpdate) -> User:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def change_password(self, user: User, data: PasswordChange) -> None:
        if not verify_password(data.current_password, user.hashed_password):
            raise AuthenticationError("当前密码不正确")
        user.hashed_password = hash_password(data.new_password)
        await self.db.commit()

    # ── Forgot / Reset Password ────────────────────────────────────

    async def forgot_password(self, email: str) -> None:
        """Send a password-reset link to the given email (if it exists)."""
        user = await self.get_by_email(email)
        if not user or not user.is_verified:
            # Don't leak whether email exists
            logger.info("Forgot-password requested for %s (skipped)", email)
            return

        r = _get_redis()
        try:
            rate_key = pwd_reset_rate_key(email)
            if await r.exists(rate_key):
                ttl = await r.ttl(rate_key)
                raise ValidationError(f"发送太频繁，请 {ttl} 秒后再试")

            token = secrets.token_urlsafe(32)
            await r.setex(pwd_reset_key(token), 1800, email)  # 30 min
            await r.setex(rate_key, settings.VERIFY_CODE_RATE_LIMIT, "1")
        finally:
            await r.aclose()

        locale = getattr(user, "language", "zh") or "zh"
        reset_url = (
            f"{settings.FRONTEND_URL}/{locale}/auth/reset-password?token={token}"
        )
        await send_reset_password_email(email, reset_url, user.name)
        logger.info("Password reset link sent to %s", email)

    async def reset_password(self, token: str, new_password: str) -> None:
        """Verify reset token and update user password."""
        r = _get_redis()
        try:
            email = await r.get(pwd_reset_key(token))
            if not email:
                raise ValidationError("重置链接已过期或无效，请重新申请")
            await r.delete(pwd_reset_key(token))
        finally:
            await r.aclose()

        user = await self.get_by_email(email)
        if not user:
            raise ValidationError("用户不存在")

        user.hashed_password = hash_password(new_password)
        await self.db.commit()
        logger.info("Password reset for %s", email)
