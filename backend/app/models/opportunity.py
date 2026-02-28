"""Opportunity ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Opportunity(Base):
    __tablename__ = "opportunities"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_opp_source_external_id"),
        Index("idx_opp_source_status", "source", "status"),
        Index("idx_opp_source_published", "source", "published_at"),
        Index("idx_opp_deadline", "deadline"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    external_id: Mapped[str | None] = mapped_column(String(100), index=True)
    url: Mapped[str | None] = mapped_column(String(500))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    project_number: Mapped[str | None] = mapped_column(String(100), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    organization: Mapped[str | None] = mapped_column(String(200))
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    budget_min: Mapped[float | None] = mapped_column(Numeric(15, 2))
    budget_max: Mapped[float | None] = mapped_column(Numeric(15, 2))
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, server_default="USD"
    )
    location: Mapped[str | None] = mapped_column(String(300))
    country: Mapped[str | None] = mapped_column(String(100), index=True)
    sector: Mapped[str | None] = mapped_column(String(100), index=True)
    procurement_type: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="open"
    )
    search_vector = mapped_column(TSVECTOR)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
