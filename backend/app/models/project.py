"""Project ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        Index("idx_proj_user_status", "user_id", "status"),
        Index("idx_proj_institution", "institution"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="draft"
    )
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("opportunities.id", ondelete="SET NULL"),
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    progress: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    current_step: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="upload"
    )
    workflow_state: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    institution: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="adb"
    )
    is_saved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    combined_ai_overview: Mapped[str | None] = mapped_column(Text)
    combined_ai_reading_tips: Mapped[str | None] = mapped_column(Text)
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
    user = relationship("User", back_populates="projects", lazy="selectin")
    opportunity = relationship("Opportunity", lazy="selectin")
    bid_documents = relationship(
        "BidDocument", back_populates="project", lazy="selectin"
    )
    project_documents = relationship(
        "ProjectDocument", back_populates="project", lazy="selectin"
    )
    bid_analysis = relationship(
        "BidAnalysis", back_populates="project", uselist=False, lazy="selectin"
    )
