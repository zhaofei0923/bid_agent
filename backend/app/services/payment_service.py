"""Payment service — credits, recharge, transactions."""

import logging
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InsufficientCreditsError, NotFoundError
from app.models.payment import (
    PaymentOrder,
    PaymentTransaction,
    RechargePackage,
)
from app.models.user import User

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for credits management and payment processing."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_balance(self, user_id: UUID) -> Decimal:
        """Get user's current credits balance."""
        result = await self.db.execute(
            select(User.credits_balance).where(User.id == user_id)
        )
        balance = result.scalar_one_or_none()
        if balance is None:
            raise NotFoundError("User", str(user_id))
        return Decimal(str(balance))

    async def deduct_credits(
        self,
        user_id: UUID,
        amount: int,
        description: str = "",
        reference_type: str = "",
        reference_id: str = "",
    ) -> Decimal:
        """Deduct credits from user balance.

        Raises InsufficientCreditsError if balance is too low.
        Returns new balance.
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User", str(user_id))

        current = Decimal(str(user.credits_balance or 0))
        if current < amount:
            raise InsufficientCreditsError(
                required=amount,
                available=int(current),
            )

        balance_before = int(current)
        user.credits_balance = int(current - amount)
        user.updated_at = datetime.now(UTC)

        # Record transaction
        txn = PaymentTransaction(
            user_id=user_id,
            type="deduction",
            amount=-amount,
            balance_before=balance_before,
            balance_after=user.credits_balance,
            description=description or None,
            related_type=reference_type or None,
        )
        self.db.add(txn)
        await self.db.commit()

        logger.info(
            "Deducted %d credits from user %s (balance: %d)",
            amount, user_id, user.credits_balance,
        )
        return Decimal(str(user.credits_balance))

    async def add_credits(
        self,
        user_id: UUID,
        amount: int,
        description: str = "",
        reference_type: str = "",
        reference_id: str = "",
    ) -> Decimal:
        """Add credits to user balance (recharge)."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User", str(user_id))

        balance_before = user.credits_balance or 0
        user.credits_balance = balance_before + amount
        user.updated_at = datetime.now(UTC)

        txn = PaymentTransaction(
            user_id=user_id,
            type="recharge",
            amount=amount,
            balance_before=balance_before,
            balance_after=user.credits_balance,
            description=description or None,
            related_type=reference_type or None,
        )
        self.db.add(txn)
        await self.db.commit()

        logger.info(
            "Added %d credits to user %s (balance: %d)",
            amount, user_id, user.credits_balance,
        )
        return Decimal(str(user.credits_balance))

    async def list_transactions(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[PaymentTransaction]:
        """List credit transactions for a user."""
        result = await self.db.execute(
            select(PaymentTransaction)
            .where(PaymentTransaction.user_id == user_id)
            .order_by(PaymentTransaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_packages(self) -> list[RechargePackage]:
        """List available recharge packages."""
        result = await self.db.execute(
            select(RechargePackage)
            .where(RechargePackage.is_active == True)  # noqa: E712
            .order_by(RechargePackage.credit_amount)
        )
        return list(result.scalars().all())

    async def create_order(
        self,
        user_id: UUID,
        package_id: UUID,
    ) -> PaymentOrder:
        """Create a payment order for credits recharge."""
        result = await self.db.execute(
            select(RechargePackage).where(RechargePackage.id == package_id)
        )
        package = result.scalar_one_or_none()
        if not package:
            raise NotFoundError("RechargePackage", str(package_id))

        order = PaymentOrder(
            user_id=user_id,
            package_id=package_id,
            amount=package.price,
            credits=package.credits,
            status="pending",
        )
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        return order
