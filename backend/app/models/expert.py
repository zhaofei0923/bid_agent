"""Expert management ORM models."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None


class Expert(Base):
    __tablename__ = "experts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    name_en: Mapped[str | None] = mapped_column(String(200))
    title: Mapped[str | None] = mapped_column(String(200))
    nationality: Mapped[str | None] = mapped_column(String(100))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    email: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(50))
    education_level: Mapped[str | None] = mapped_column(String(50))
    education_details: Mapped[dict | None] = mapped_column(JSONB)
    certifications: Mapped[dict | None] = mapped_column(JSONB)
    professional_memberships: Mapped[dict | None] = mapped_column(JSONB)
    languages: Mapped[dict | None] = mapped_column(JSONB)
    total_experience_years: Mapped[int | None] = mapped_column(Integer)
    sector_experience: Mapped[dict | None] = mapped_column(JSONB)
    region_experience: Mapped[dict | None] = mapped_column(JSONB)
    project_history: Mapped[dict | None] = mapped_column(JSONB)
    adb_project_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    wb_project_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    total_project_value: Mapped[float | None] = mapped_column(Float)
    cv_summary: Mapped[str | None] = mapped_column(Text)
    cv_full_text: Mapped[str | None] = mapped_column(Text)
    cv_file_path: Mapped[str | None] = mapped_column(String(500))
    cv_embedding = mapped_column(Vector(1024) if Vector else Text, nullable=True)
    skills_embedding = mapped_column(Vector(1024) if Vector else Text, nullable=True)
    internal_rating: Mapped[float | None] = mapped_column(Float)
    availability_score: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="1.0"
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="active", index=True
    )
    current_project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL")
    )
    available_from: Mapped[date | None] = mapped_column(Date)
    tags = mapped_column(ARRAY(String), nullable=True)
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
    skills = relationship("ExpertSkill", back_populates="expert", lazy="selectin")


class SkillTag(Base):
    __tablename__ = "skill_tags"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    name_en: Mapped[str | None] = mapped_column(String(200))
    category: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    embedding = mapped_column(Vector(1024) if Vector else Text, nullable=True)


class ExpertSkill(Base):
    __tablename__ = "expert_skills"

    expert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skill_tags.id", ondelete="CASCADE"),
        primary_key=True,
    )
    proficiency_level: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="3"
    )
    years_experience: Mapped[int | None] = mapped_column(Integer)

    # Relationships
    expert = relationship("Expert", back_populates="skills")
    skill = relationship("SkillTag")


class TeamAssignment(Base):
    __tablename__ = "team_assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    role_type: Mapped[str | None] = mapped_column(String(50))
    position: Mapped[str | None] = mapped_column(String(200))
    responsibilities: Mapped[str | None] = mapped_column(Text)
    person_months: Mapped[float | None] = mapped_column(Float)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_home_based: Mapped[bool] = mapped_column(server_default="false", nullable=False)
    location: Mapped[str | None] = mapped_column(String(200))
    match_score: Mapped[float | None] = mapped_column(Float)
    match_reasons: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="proposed"
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


class ExpertMatchResult(Base):
    __tablename__ = "expert_match_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requirements_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    matched_experts: Mapped[dict | None] = mapped_column(JSONB)
    team_composition: Mapped[dict | None] = mapped_column(JSONB)
    algorithm_version: Mapped[str | None] = mapped_column(String(50))
    matching_criteria: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
