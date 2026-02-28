"""Project document ORM models: ProjectDocument, ProjectDocumentChunk."""

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


class ProjectDocument(Base):
    __tablename__ = "project_documents"
    __table_args__ = (
        Index("idx_pd_project_type", "project_id", "doc_type"),
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
    mime_type: Mapped[str] = mapped_column(
        String(100), nullable=False, server_default="application/pdf"
    )
    file_hash: Mapped[str | None] = mapped_column(String(64))
    doc_type: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="other"
    )
    parse_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    parse_error: Mapped[str | None] = mapped_column(Text)
    parsed_content: Mapped[str | None] = mapped_column(Text)
    ocr_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    ocr_confidence: Mapped[float | None] = mapped_column(Float)
    embedding_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    page_count: Mapped[int | None] = mapped_column(Integer)
    language: Mapped[str | None] = mapped_column(String(10))
    doc_metadata: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default="{}"
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
    project = relationship("Project", back_populates="project_documents")
    chunks = relationship("ProjectDocumentChunk", back_populates="document")


class ProjectDocumentChunk(Base):
    __tablename__ = "project_document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer)
    start_char: Mapped[int | None] = mapped_column(Integer)
    end_char: Mapped[int | None] = mapped_column(Integer)
    embedding = mapped_column(Vector(1024) if Vector else Text, nullable=True)
    chunk_metadata: Mapped[dict | None] = mapped_column(JSONB, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    document = relationship("ProjectDocument", back_populates="chunks")
