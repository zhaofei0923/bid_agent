"""Opportunity service — listing, searching, CRUD."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import ClassVar
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.opportunity import Opportunity
from app.schemas.opportunity import OpportunityQuery, PaginatedOpportunities


class OpportunityService:
    SORT_COLUMNS: ClassVar[dict[str, object]] = {
        "published_at": Opportunity.published_at,
        "deadline": Opportunity.deadline,
        "created_at": Opportunity.created_at,
        "updated_at": Opportunity.updated_at,
        "title": Opportunity.title,
        "source": Opportunity.source,
        "country": Opportunity.country,
        "sector": Opportunity.sector,
    }

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list(self, query: OpportunityQuery) -> PaginatedOpportunities:
        stmt = select(Opportunity)
        now = datetime.now(UTC)

        if query.source:
            stmt = stmt.where(Opportunity.source == query.source)
        # Default to open-only; explicitly pass status=all to include expired/closed
        if query.status and query.status != "all":
            stmt = stmt.where(Opportunity.status == query.status)
        elif not query.status:
            stmt = stmt.where(Opportunity.status == "open")
        if query.status in (None, "open"):
            stmt = stmt.where(
                or_(Opportunity.deadline.is_(None), Opportunity.deadline >= now)
            )
        if query.country:
            stmt = stmt.where(Opportunity.country == query.country)
        if query.sector:
            stmt = stmt.where(Opportunity.sector == query.sector)
        if query.published_from:
            stmt = stmt.where(Opportunity.published_at >= query.published_from)
        if query.published_to:
            stmt = stmt.where(Opportunity.published_at <= query.published_to)
        if query.deadline_from:
            stmt = stmt.where(Opportunity.deadline >= query.deadline_from)
        if query.deadline_to:
            stmt = stmt.where(Opportunity.deadline <= query.deadline_to)
        if query.search:
            stmt = stmt.where(
                Opportunity.search_vector.op("@@")(
                    func.plainto_tsquery("english", query.search)
                )
            )

        # Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        # Sort
        sort_col = self.SORT_COLUMNS.get(query.sort_by, Opportunity.published_at)
        if query.sort_order == "asc":
            stmt = stmt.order_by(sort_col.asc())
        else:
            stmt = stmt.order_by(sort_col.desc())

        # Paginate
        offset = (query.page - 1) * query.page_size
        stmt = stmt.offset(offset).limit(query.page_size)

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return PaginatedOpportunities(
            items=items,
            total=total,
            page=query.page,
            page_size=query.page_size,
            total_pages=math.ceil(total / query.page_size) if total > 0 else 0,
        )

    async def get_by_id(self, opportunity_id: UUID) -> Opportunity:
        result = await self.db.execute(
            select(Opportunity).where(Opportunity.id == opportunity_id)
        )
        opp = result.scalar_one_or_none()
        if not opp:
            raise NotFoundError("Opportunity", str(opportunity_id))
        return opp

    async def latest(
        self,
        limit: int = 10,
        source: str | None = None,
    ) -> list[Opportunity]:
        """Return the most recently published open opportunities."""
        stmt = (
            select(Opportunity)
            .where(Opportunity.status == "open")
            .where(
                or_(
                    Opportunity.deadline.is_(None),
                    Opportunity.deadline >= datetime.now(UTC),
                )
            )
            .order_by(Opportunity.published_at.desc())
            .limit(limit)
        )
        if source:
            stmt = stmt.where(Opportunity.source == source)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
