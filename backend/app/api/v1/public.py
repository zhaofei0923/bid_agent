"""Public API routes — no authentication required."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.opportunity import (
    OpportunityQuery,
    PaginatedPublicOpportunities,
    PublicOpportunityQuery,
)
from app.services.opportunity_service import OpportunityService

router = APIRouter()


@router.get("/opportunities", response_model=PaginatedPublicOpportunities)
async def public_search_opportunities(
    search: str | None = None,
    source: str | None = None,
    country: str | None = None,
    sector: str | None = None,
    sort_by: str = "published_at",
    sort_order: str = "desc",
    page: int = Query(1, ge=1, le=5),
    page_size: int = Query(20, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Search open opportunities — free, no login required.

    - Only returns opportunities with status='open'.
    - Max 5 pages (100 results) to encourage registration.
    """
    # Validate via public schema (applies le constraints)
    try:
        pub_query = PublicOpportunityQuery(
            search=search,
            source=source,
            country=country,
            sector=sector,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(),
        ) from exc

    # Convert to internal OpportunityQuery with forced status=open
    query = OpportunityQuery(
        search=pub_query.search,
        source=pub_query.source,
        status="open",
        country=pub_query.country,
        sector=pub_query.sector,
        sort_by=pub_query.sort_by,
        sort_order=pub_query.sort_order,
        page=pub_query.page,
        page_size=pub_query.page_size,
    )

    service = OpportunityService(db)
    return await service.list(query)


@router.get("/opportunities/latest")
async def public_latest_opportunities(
    limit: int = Query(10, ge=1, le=30),
    source: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Return the latest open opportunities for landing page / dashboard.

    - Sorted by published_at desc.
    - No pagination; returns up to `limit` items.
    - Optionally filter by source (adb/wb/afdb).
    """
    service = OpportunityService(db)
    return await service.latest(limit=limit, source=source)
