"""Admin request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ── Request Schemas ──────────────────────────────────────────────


class AdminCreditAdjustRequest(BaseModel):
    """Adjust a user's credit balance (positive = add, negative = deduct)."""

    amount: int = Field(
        ...,
        description="Positive to add credits, negative to deduct. Cannot be zero.",
    )
    reason: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Reason for the adjustment (shown in transaction history).",
    )

    def validate_amount(self) -> None:
        if self.amount == 0:
            raise ValueError("amount cannot be zero")


class AdminUserRoleUpdate(BaseModel):
    role: str = Field(..., pattern="^(user|admin)$")


# ── Response Schemas ─────────────────────────────────────────────


class AdminUserListItem(BaseModel):
    id: UUID
    email: str
    name: str
    company: str | None
    role: str
    credits_balance: int
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUserListResponse(BaseModel):
    items: list[AdminUserListItem]
    total: int
    page: int
    page_size: int
    pages: int


class AdminTransactionItem(BaseModel):
    id: UUID
    type: str
    amount: float
    balance_before: float
    balance_after: float
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminCreditAdjustResponse(BaseModel):
    new_balance: int
    transaction_id: UUID
