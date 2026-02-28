"""Knowledge base request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    institution: str = Field(pattern="^(adb|wb|un)$")
    kb_type: str = Field(pattern="^(guide|review|template)$")
    description: str | None = None


class KnowledgeBaseResponse(BaseModel):
    id: UUID
    name: str
    institution: str
    kb_type: str
    description: str | None = None
    document_count: int
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeDocumentResponse(BaseModel):
    id: UUID
    knowledge_base_id: UUID
    filename: str
    file_size: int | None = None
    status: str
    error_message: str | None = None
    page_count: int | None = None
    chunk_count: int
    created_at: datetime
    processed_at: datetime | None = None

    model_config = {"from_attributes": True}


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    institution: str | None = Field(None, pattern="^(adb|wb|un)$")
    kb_type: str | None = Field(None, pattern="^(guide|review|template)$")
    top_k: int = Field(5, ge=1, le=20)
    score_threshold: float = Field(0.5, ge=0, le=1)


class KnowledgeSearchResult(BaseModel):
    content: str
    score: float
    source_document: str
    page_number: int | None = None
