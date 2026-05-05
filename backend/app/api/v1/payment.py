"""Payment and credits API routes."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.services.payment_service import PaymentService

if TYPE_CHECKING:
    from app.models.payment import RechargePackage

router = APIRouter()


class CreateOrderRequest(BaseModel):
    """Request body for creating a payment order."""

    package_id: UUID
    payment_method: str = Field("alipay", pattern="^(alipay|wechat|bank_transfer)$")


class PackageResponse(BaseModel):
    """Response schema for recharge packages."""

    id: UUID
    name: str
    description: str | None = None
    credits: int
    price: float
    currency: str
    is_active: bool
    sort_order: int
    bonus_credits: int
    bonus_description: str | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, obj: RechargePackage) -> PackageResponse:
        return cls(
            id=obj.id,
            name=obj.name,
            description=obj.description,
            credits=obj.credit_amount,
            price=float(obj.price),
            currency=obj.currency,
            is_active=obj.is_active,
            sort_order=obj.sort_order,
            bonus_credits=obj.bonus_credits,
            bonus_description=obj.bonus_description,
        )


@router.get("/balance")
async def get_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's credit balance."""
    service = PaymentService(db)
    balance = await service.get_balance(current_user.id)
    return {"balance": balance}


@router.get("/transactions")
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's credit transactions."""
    service = PaymentService(db)
    offset = (page - 1) * page_size
    return await service.list_transactions(
        current_user.id, limit=page_size, offset=offset
    )


@router.get("/packages", response_model=list[PackageResponse])
async def list_packages(
    db: AsyncSession = Depends(get_db),
):
    """List available recharge packages."""
    service = PaymentService(db)
    packages = await service.list_packages()
    return [PackageResponse.from_orm_model(p) for p in packages]


@router.post("/orders")
async def create_order(
    request: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a payment order for a recharge package."""
    service = PaymentService(db)
    return await service.create_order(
        current_user.id, request.package_id, request.payment_method
    )
