"""Bid document request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class BidDocumentResponse(BaseModel):
    id: UUID
    project_id: UUID
    filename: str
    original_filename: str
    file_size: int | None = None
    file_hash: str | None = None
    status: str
    processing_progress: int
    page_count: int | None = None
    processed_pages: int
    chunk_count: int
    vectorized_chunk_count: int
    error_message: str | None = None
    is_scanned: bool
    ocr_confidence: float | None = None
    original_language: str
    ai_overview: str | None = None
    ai_reading_tips: str | None = None
    detected_institution: str | None = None
    analysis_generated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BidDocumentSectionResponse(BaseModel):
    id: UUID
    bid_document_id: UUID
    section_type: str
    section_title: str | None = None
    section_number: str | None = None
    start_page: int
    end_page: int
    content_preview: str | None = None
    detected_by: str
    confidence: float | None = None
    ai_summary: str | None = None
    reading_guide: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
