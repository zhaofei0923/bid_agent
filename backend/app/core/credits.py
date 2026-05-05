"""Credits deduction dependency and middleware utilities.

Provides:
- ``require_credits``: FastAPI dependency that checks balance *before* the
  endpoint runs and deducts credits *after* via a background task / response hook.
- ``add_credits_headers``: Add ``X-Credits-Consumed`` / ``X-Credits-Remaining``
  to any response.

Pricing table (per 05-agent-workflow §6):
  - bid_analysis_trigger: 20 credits
  - guidance_qa: 5 credits
  - guidance_stream: 8 credits
  - quality_review_full: 30 credits
  - quality_review_quick: 10 credits
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InsufficientCreditsError
from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)

# ── Pricing Constants ────────────────────────────────────────
CREDIT_COST: dict[str, int] = {
    "bid_analysis_trigger": 20,
    "guidance_qa": 5,
    "guidance_stream": 8,
    "quality_review_full": 30,
    "quality_review_quick": 10,
    "doc_review_item": 5,
}


# ── Core Functions ───────────────────────────────────────────

async def check_credits(
    user: User,
    action: str,
    db: AsyncSession,
) -> int:
    """Check that user has enough credits for *action*. Returns cost.

    Raises:
        InsufficientCreditsError: if balance < cost.
        KeyError: if action is unknown.
    """
    cost = CREDIT_COST.get(action)
    if cost is None:
        raise KeyError(f"Unknown billable action: {action}")

    balance = user.credits_balance or 0
    if balance < cost:
        raise InsufficientCreditsError(required=cost, available=balance)
    return cost


async def deduct_credits(
    user: User,
    action: str,
    cost: int,
    db: AsyncSession,
    *,
    reference_id: str | None = None,
) -> int:
    """Atomically deduct *cost* credits from user and log a transaction.

    Returns the new balance.
    """
    service = PaymentService(db)
    new_balance_decimal = await service.deduct_credits(
        user_id=user.id,
        amount=cost,
        description=f"[{action}] 操作消耗",
        reference_type=action,
        reference_id=reference_id or "",
    )
    new_balance = int(new_balance_decimal)

    logger.info(
        "Credits deducted: user=%s action=%s cost=%d balance=%d",
        user.id,
        action,
        cost,
        new_balance,
    )
    return new_balance


def add_credits_headers(
    response: Response,
    consumed: int,
    remaining: int,
) -> None:
    """Attach credit tracking headers to response."""
    response.headers["X-Credits-Consumed"] = str(consumed)
    response.headers["X-Credits-Remaining"] = str(remaining)


# ── Dependency Factories ─────────────────────────────────────

def require_credits(action: str):
    """FastAPI dependency factory that guards an endpoint with credits check.

    Usage::

        @router.post("/analysis/trigger")
        async def trigger(
            cost_info: dict = Depends(require_credits("bid_analysis_trigger")),
            ...
        ):
            # cost_info = {"cost": 20, "action": "bid_analysis_trigger"}
    """

    async def _check(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
        cost = await check_credits(current_user, action, db)
        return {"cost": cost, "action": action, "user": current_user, "db": db}

    return _check
