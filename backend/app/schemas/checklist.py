"""Submission checklist schemas — structured bid document submission requirements."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChecklistSource(BaseModel):
    """Source citation from the tender document."""

    filename: str = ""
    page_number: int | None = None
    section_title: str = ""
    excerpt: str = Field(default="", description="Original text excerpt (≤150 chars)")


class ChecklistItem(BaseModel):
    """A single document/material to be submitted."""

    id: str
    title: str
    required: bool = True
    copies: int | None = None
    format_hint: str | None = None
    guidance: str = Field(
        default="",
        description="Chinese writing guidance (~100 chars), tells user what to include",
    )
    source: ChecklistSource = Field(default_factory=ChecklistSource)


class ChecklistSection(BaseModel):
    """A grouping of related checklist items (e.g., Technical Proposal)."""

    id: str
    title: str
    icon: str = "📄"
    items: list[ChecklistItem] = Field(default_factory=list)


class SubmissionChecklistResponse(BaseModel):
    """Response for the submission checklist endpoint."""

    project_id: UUID
    institution: str
    sections: list[ChecklistSection]
    generated_at: datetime
    cached: bool = False
