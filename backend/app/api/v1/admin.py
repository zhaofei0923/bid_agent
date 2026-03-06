"""Admin API routes — user management & credit adjustment.

All routes require `admin` role (enforced by require_admin dependency).
"""

from __future__ import annotations

import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_admin
from app.database import get_db
from app.models.payment import PaymentTransaction
from app.models.user import User
from app.schemas.admin import (
    AdminCreditAdjustRequest,
    AdminCreditAdjustResponse,
    AdminTransactionItem,
    AdminUserListItem,
    AdminUserListResponse,
    AdminUserRoleUpdate,
)
from app.services.payment_service import PaymentService

router = APIRouter()


# ── User List ────────────────────────────────────────────────────


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    search: str | None = Query(None, description="Filter by email or name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserListResponse:
    """Return paginated list of all users, optionally filtered by email/name."""
    base_query = select(User)
    count_query = select(func.count()).select_from(User)

    if search:
        like = f"%{search}%"
        condition = or_(User.email.ilike(like), User.name.ilike(like))
        base_query = base_query.where(condition)
        count_query = count_query.where(condition)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    users_result = await db.execute(
        base_query.order_by(User.created_at.desc()).offset(offset).limit(page_size)
    )
    users = users_result.scalars().all()

    return AdminUserListResponse(
        items=[AdminUserListItem.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 1,
    )


# ── User Detail ──────────────────────────────────────────────────


@router.get("/users/{user_id}", response_model=AdminUserListItem)
async def get_user(
    user_id: UUID,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserListItem:
    """Return a single user's details."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return AdminUserListItem.model_validate(user)


# ── Credit Adjustment ───────────────────────────────────────────


@router.post("/users/{user_id}/credits/adjust", response_model=AdminCreditAdjustResponse)
async def adjust_credits(
    user_id: UUID,
    body: AdminCreditAdjustRequest,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminCreditAdjustResponse:
    """Add or deduct credits for a user.

    Positive `amount` → add credits.
    Negative `amount` → deduct credits.
    """
    if body.amount == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="amount cannot be zero",
        )

    service = PaymentService(db)

    if body.amount > 0:
        new_balance = await service.add_credits(
            user_id,
            body.amount,
            description=body.reason,
            reference_type="admin_adjust",
        )
    else:
        new_balance = await service.deduct_credits(
            user_id,
            abs(body.amount),
            description=body.reason,
            reference_type="admin_adjust",
        )

    # Retrieve the latest transaction id for this user
    txn_result = await db.execute(
        select(PaymentTransaction)
        .where(PaymentTransaction.user_id == user_id)
        .order_by(PaymentTransaction.created_at.desc())
        .limit(1)
    )
    txn = txn_result.scalar_one()

    return AdminCreditAdjustResponse(
        new_balance=int(new_balance),
        transaction_id=txn.id,
    )


# ── Transaction History ──────────────────────────────────────────


@router.get("/users/{user_id}/transactions", response_model=list[AdminTransactionItem])
async def list_transactions(
    user_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminTransactionItem]:
    """Return paginated credit transaction history for a user."""
    # Verify user exists
    user_result = await db.execute(select(User.id).where(User.id == user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    offset = (page - 1) * page_size
    txn_result = await db.execute(
        select(PaymentTransaction)
        .where(PaymentTransaction.user_id == user_id)
        .order_by(PaymentTransaction.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    txns = txn_result.scalars().all()
    return [AdminTransactionItem.model_validate(t) for t in txns]


# ── Role Update ──────────────────────────────────────────────────


@router.put("/users/{user_id}/role", response_model=AdminUserListItem)
async def update_user_role(
    user_id: UUID,
    body: AdminUserRoleUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserListItem:
    """Change a user's role (user ↔ admin)."""
    if str(user_id) == str(admin.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.role = body.role
    await db.commit()
    await db.refresh(user)
    return AdminUserListItem.model_validate(user)
