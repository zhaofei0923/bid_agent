"""Guidance (bid coaching) request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class GuidanceRequest(BaseModel):
    """User message in the guidance chat."""

    message: str = Field(min_length=1)
    context_type: str | None = None  # section_guidance / review_draft / qa
    section_type: str | None = None  # target section (if any)
    draft_content: str | None = None  # user's draft text (for review)


class GuidanceResponse(BaseModel):
    """AI guidance response."""

    id: UUID
    project_id: UUID
    role: str  # "assistant"
    content: str
    skill_used: str | None = None
    sources: list[dict] | None = None
    tokens_consumed: int
    created_at: datetime

    model_config = {"from_attributes": True}
