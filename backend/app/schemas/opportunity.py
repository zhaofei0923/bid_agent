"""Opportunity request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OpportunityQuery(BaseModel):
    """Query parameters for opportunity listing."""

    search: str | None = None
    source: str | None = Field(None, pattern="^(adb|wb|afdb)$")
    status: str | None = Field(None, pattern="^(open|closed|cancelled|all)$")
    published_from: datetime | None = None
    published_to: datetime | None = None
    deadline_from: datetime | None = None
    deadline_to: datetime | None = None
    country: str | None = None
    sector: str | None = None
    sort_by: str = Field(
        "published_at",
        pattern="^(published_at|deadline|created_at|updated_at|title|source|country|sector)$",
    )
    sort_order: str = Field("desc", pattern="^(asc|desc)$")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class OpportunityResponse(BaseModel):
    id: UUID
    source: str
    external_id: str | None = None
    url: str | None = None
    title: str
    project_number: str | None = None
    description: str | None = None
    organization: str | None = None
    published_at: datetime | None = None
    deadline: datetime | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    currency: str
    location: str | None = None
    country: str | None = None
    sector: str | None = None
    procurement_type: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedOpportunities(BaseModel):
    items: list[OpportunityResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ── Public (no-auth) schemas ──────────────────────────────────


class PublicOpportunityQuery(BaseModel):
    """Query parameters for public opportunity search (no auth required)."""

    search: str | None = None
    source: str | None = Field(None, pattern="^(adb|wb|afdb)$")
    country: str | None = None
    sector: str | None = None
    sort_by: str = Field(
        "published_at",
        pattern="^(published_at|deadline|created_at|updated_at|title|source|country|sector)$",
    )
    sort_order: str = Field("desc", pattern="^(asc|desc)$")
    page: int = Field(1, ge=1, le=5)
    page_size: int = Field(20, ge=1, le=20)


class PublicOpportunityResponse(BaseModel):
    """Opportunity fields exposed publicly (excludes external_id)."""

    id: UUID
    source: str
    url: str | None = None
    title: str
    project_number: str | None = None
    description: str | None = None
    organization: str | None = None
    published_at: datetime | None = None
    deadline: datetime | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    currency: str
    location: str | None = None
    country: str | None = None
    sector: str | None = None
    procurement_type: str | None = None
    status: str

    model_config = {"from_attributes": True}


class PaginatedPublicOpportunities(BaseModel):
    items: list[PublicOpportunityResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
