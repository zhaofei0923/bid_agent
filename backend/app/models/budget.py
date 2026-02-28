"""Budget management ORM models."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UnitPriceItem(Base):
    __tablename__ = "unit_price_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    name_en: Mapped[str | None] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="other", index=True
    )
    unit: Mapped[str | None] = mapped_column(String(50))
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="USD"
    )
    min_price: Mapped[float | None] = mapped_column(Float)
    max_price: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str | None] = mapped_column(String(200))
    effective_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    applicable_regions = mapped_column(ARRAY(String), nullable=True)
    applicable_sectors = mapped_column(ARRAY(String), nullable=True)
    applicable_institutions = mapped_column(ARRAY(String), nullable=True)
    tags = mapped_column(ARRAY(String), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ExpertRate(Base):
    __tablename__ = "expert_rates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    level: Mapped[str] = mapped_column(String(100), nullable=False)
    level_en: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    monthly_rate: Mapped[float] = mapped_column(Float, nullable=False)
    daily_rate: Mapped[float | None] = mapped_column(Float)
    hourly_rate: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="USD"
    )
    min_rate: Mapped[float | None] = mapped_column(Float)
    max_rate: Mapped[float | None] = mapped_column(Float)
    years_experience_min: Mapped[int | None] = mapped_column(Integer)
    years_experience_max: Mapped[int | None] = mapped_column(Integer)
    applicable_positions = mapped_column(ARRAY(String), nullable=True)
    applicable_institutions = mapped_column(ARRAY(String), nullable=True)
    effective_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ProjectBudget(Base):
    __tablename__ = "project_budgets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="1"
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="draft"
    )
    total_amount: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="USD"
    )
    remuneration_total: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0"
    )
    reimbursable_total: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0"
    )
    equipment_total: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0"
    )
    subcontract_total: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0"
    )
    contingency_total: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0"
    )
    overhead_total: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0"
    )
    budget_items: Mapped[dict | None] = mapped_column(JSONB)
    estimation_basis: Mapped[dict | None] = mapped_column(JSONB)
    assumptions: Mapped[dict | None] = mapped_column(JSONB)
    ai_suggestions: Mapped[dict | None] = mapped_column(JSONB)
    ai_warnings: Mapped[dict | None] = mapped_column(JSONB)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class BudgetItem(Base):
    __tablename__ = "budget_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    budget_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_budgets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str | None] = mapped_column(String(50))
    quantity: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="1"
    )
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="USD"
    )
    unit_price_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("unit_price_items.id", ondelete="SET NULL"),
    )
    expert_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experts.id", ondelete="SET NULL"),
    )
    notes: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
