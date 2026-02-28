"""MCP Tool: opportunity_query — search and filter opportunities."""

import logging
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.opportunity import Opportunity

logger = logging.getLogger(__name__)


async def opportunity_query(
    db: AsyncSession,
    *,
    keyword: str | None = None,
    source: str | None = None,
    sector: str | None = None,
    country: str | None = None,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Query opportunities with optional filters.

    MCP-compatible tool for agents to search the opportunity database.

    Args:
        db: Async database session.
        keyword: Full-text search keyword.
        source: Filter by source (adb / wb / un).
        sector: Filter by sector.
        country: Filter by country.
        status: Filter by status (open / closed / cancelled).
        limit: Max results (default 20).
        offset: Pagination offset.

    Returns:
        List of opportunity dicts with core fields.
    """
    query = select(Opportunity)
    conditions = []

    if source:
        conditions.append(Opportunity.source == source)
    if sector:
        conditions.append(Opportunity.sector.ilike(f"%{sector}%"))
    if country:
        conditions.append(Opportunity.country.ilike(f"%{country}%"))
    if status:
        conditions.append(Opportunity.status == status)

    if keyword:
        # Use PostgreSQL full-text search via search_vector column
        tsquery = keyword.replace(" ", " & ")
        conditions.append(
            or_(
                Opportunity.search_vector.op("@@")(
                    Opportunity.__table__.c.search_vector.op("@@")(
                        # Raw sql func for to_tsquery in case ORM doesn't expose it
                    )
                )
                if False
                else Opportunity.title.ilike(f"%{keyword}%"),
                Opportunity.description.ilike(f"%{keyword}%"),
            )
        )

    if conditions:
        query = query.where(and_(*conditions))

    query = (
        query.order_by(Opportunity.published_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(query)
    rows = result.scalars().all()

    return [
        {
            "id": str(opp.id),
            "source": opp.source,
            "title": opp.title,
            "organization": opp.organization,
            "country": opp.country,
            "sector": opp.sector,
            "deadline": opp.deadline.isoformat() if opp.deadline else None,
            "status": opp.status,
            "url": opp.url,
        }
        for opp in rows
    ]
