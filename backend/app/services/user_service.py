"""User service — registration, authentication, profile management."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
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
    TokenResponse,
    UserRegister,
    UserUpdate,
)


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

    async def register(self, data: UserRegister) -> TokenResponse:
        existing = await self.get_by_email(data.email)
        if existing:
            raise ValidationError("Email already registered")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            name=data.name,
            company=data.company,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

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

    async def update_profile(self, user: User, data: UserUpdate) -> User:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def change_password(self, user: User, data: PasswordChange) -> None:
        if not verify_password(data.current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect")
        user.hashed_password = hash_password(data.new_password)
        await self.db.commit()
