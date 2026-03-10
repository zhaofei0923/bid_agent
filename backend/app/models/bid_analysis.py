"""Bid analysis and prediction ORM models."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BidAnalysis(Base):
    __tablename__ = "bid_analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    executive_summary: Mapped[dict | None] = mapped_column(JSONB)
    qualification_requirements: Mapped[dict | None] = mapped_column(JSONB)
    evaluation_criteria: Mapped[dict | None] = mapped_column(JSONB)
    evaluation_methodology: Mapped[dict | None] = mapped_column(JSONB)
    commercial_terms: Mapped[dict | None] = mapped_column(JSONB)
    submission_checklist: Mapped[dict | None] = mapped_column(JSONB)
    key_dates: Mapped[dict | None] = mapped_column(JSONB)
    bds_modifications: Mapped[dict | None] = mapped_column(JSONB)
    technical_requirements: Mapped[dict | None] = mapped_column(JSONB)
    technical_strategy: Mapped[dict | None] = mapped_column(JSONB)
    compliance_matrix: Mapped[dict | None] = mapped_column(JSONB)
    risk_assessment: Mapped[dict | None] = mapped_column(JSONB)
    budget_info: Mapped[dict | None] = mapped_column(JSONB)
    special_notes: Mapped[str | None] = mapped_column(Text)
    quality_review: Mapped[dict | None] = mapped_column(JSONB)
    raw_analysis: Mapped[str | None] = mapped_column(Text)
    model_used: Mapped[str | None] = mapped_column(String(100))
    tokens_consumed: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
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

    # Relationships
    project = relationship("Project", back_populates="bid_analysis")


class BidPrediction(Base):
    __tablename__ = "bid_predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    overall_score: Mapped[int | None] = mapped_column(Integer)
    technical_score: Mapped[int | None] = mapped_column(Integer)
    commercial_score: Mapped[int | None] = mapped_column(Integer)
    win_probability: Mapped[int | None] = mapped_column(Integer)
    weaknesses: Mapped[dict | None] = mapped_column(JSONB)
    recommendations: Mapped[dict | None] = mapped_column(JSONB)
    competitive_analysis: Mapped[dict | None] = mapped_column(JSONB)
    analysis_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    model_used: Mapped[str | None] = mapped_column(String(100))
    confidence_level: Mapped[str | None] = mapped_column(String(20))
    analysis_version: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="1.0"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
