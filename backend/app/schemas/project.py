"""Project request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    opportunity_id: UUID | None = None
    institution: str = Field("adb", pattern="^(adb|wb|other)$")


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    status: str | None = None
    progress: int | None = Field(None, ge=0, le=100)
    current_step: str | None = None
    is_saved: bool | None = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    status: str
    opportunity_id: UUID | None = None
    user_id: UUID
    progress: int
    current_step: str
    institution: str
    is_saved: bool
    combined_ai_overview: str | None = None
    combined_ai_reading_tips: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedProjects(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int
    pages: int
