"""Bid plan and task ORM models."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BidPlan(Base):
    __tablename__ = "bid_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, server_default="投标计划"
    )
    description: Mapped[str | None] = mapped_column(Text)
    total_tasks: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    completed_tasks: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    generated_by_ai: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    model_used: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    tasks = relationship("BidPlanTask", back_populates="plan", lazy="selectin")


class BidPlanTask(Base):
    __tablename__ = "bid_plan_tasks"
    __table_args__ = (
        Index("idx_bpt_plan_sort", "plan_id", "sort_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bid_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100))
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="medium"
    )
    assignee: Mapped[str | None] = mapped_column(String(200))
    due_date: Mapped[date | None] = mapped_column(Date, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    related_document: Mapped[str | None] = mapped_column(String(500))
    reference_page: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    plan = relationship("BidPlan", back_populates="tasks")
