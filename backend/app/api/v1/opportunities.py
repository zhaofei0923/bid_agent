"""Opportunities API routes — list, detail, admin CRUD."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db
from app.schemas.opportunity import (
    OpportunityQuery,
    OpportunityResponse,
    PaginatedOpportunities,
)
from app.services.opportunity_service import OpportunityService

router = APIRouter()


@router.get("", response_model=PaginatedOpportunities)
async def list_opportunities(
    search: str | None = None,
    source: str | None = None,
    status: str | None = None,
    country: str | None = None,
    sector: str | None = None,
    sort_by: str = "published_at",
    sort_order: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OpportunityService(db)
    query = OpportunityQuery(
        search=search,
        source=source,
        status=status,
        country=country,
        sector=sector,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    return await service.list(query)


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: UUID,
    _current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OpportunityService(db)
    return await service.get_by_id(opportunity_id)
