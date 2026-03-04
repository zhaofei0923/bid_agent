"""Bid document ORM models: BidDocument, BidDocumentSection, BidDocumentChunk."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None


class BidDocument(Base):
    __tablename__ = "bid_documents"
    __table_args__ = (
        Index("idx_bd_project_status", "project_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer)
    file_hash: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    processing_progress: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    page_count: Mapped[int | None] = mapped_column(Integer)
    processed_pages: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    vectorized_chunk_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    is_scanned: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    ocr_confidence: Mapped[float | None] = mapped_column(Float)
    original_language: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="en"
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    ai_overview: Mapped[str | None] = mapped_column(Text)
    ai_reading_tips: Mapped[str | None] = mapped_column(Text)
    detected_institution: Mapped[str | None] = mapped_column(String(20), index=True)
    analysis_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
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
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    project = relationship("Project", back_populates="bid_documents")
    sections = relationship(
        "BidDocumentSection",
        back_populates="bid_document",
        lazy="selectin",
        passive_deletes=True,
    )
    chunks = relationship(
        "BidDocumentChunk",
        back_populates="bid_document",
        passive_deletes=True,
    )


class BidDocumentSection(Base):
    __tablename__ = "bid_document_sections"
    __table_args__ = (
        Index("idx_bds_doc_type", "bid_document_id", "section_type"),
        Index("idx_bds_page_range", "bid_document_id", "start_page", "end_page"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    bid_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bid_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section_type: Mapped[str] = mapped_column(String(50), nullable=False)
    section_title: Mapped[str | None] = mapped_column(String(500))
    section_number: Mapped[str | None] = mapped_column(String(20))
    start_page: Mapped[int] = mapped_column(Integer, nullable=False)
    end_page: Mapped[int] = mapped_column(Integer, nullable=False)
    content_preview: Mapped[str | None] = mapped_column(Text)
    detected_by: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="regex"
    )
    confidence: Mapped[float | None] = mapped_column(Float)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    reading_guide: Mapped[str | None] = mapped_column(Text)
    analysis_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    bid_document = relationship("BidDocument", back_populates="sections")


class BidDocumentChunk(Base):
    __tablename__ = "bid_document_chunks"
    __table_args__ = (
        Index("idx_bdc_project_section", "project_id", "section_type"),
        Index("idx_bdc_page", "bid_document_id", "page_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    bid_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bid_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bid_document_sections.id", ondelete="SET NULL"),
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_char: Mapped[int | None] = mapped_column(Integer)
    end_char: Mapped[int | None] = mapped_column(Integer)
    section_type: Mapped[str | None] = mapped_column(String(50))
    clause_reference: Mapped[str | None] = mapped_column(String(100))
    embedding = mapped_column(Vector(1024) if Vector else Text, nullable=True)
    chunk_metadata: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    bid_document = relationship("BidDocument", back_populates="chunks")
