"""Fetcher tasks — periodic opportunity fetching via API/RSS using Celery."""

import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import select

from app.database import async_session
from app.fetchers import get_fetcher
from app.fetchers.base import TenderInfo
from app.models.opportunity import Opportunity
from app.tasks import celery_app

logger = logging.getLogger(__name__)


async def _run_fetcher(source: str, max_pages: int = 5) -> dict:
    """Async implementation: fetch and upsert opportunities."""
    fetcher = get_fetcher(source)

    def _trunc(value: str | None, max_len: int = 100) -> str | None:
        """Truncate a string to fit database column limits."""
        if value and len(value) > max_len:
            return value[: max_len - 3] + "..."
        return value

    tenders: list[TenderInfo] = []
    async with fetcher:
        tenders = await fetcher.fetch_all(max_pages=max_pages, fetch_details=False)

    created = 0
    updated = 0
    skipped = 0
    now = datetime.now(UTC)

    # Statuses that represent a closed / no-longer-open opportunity
    skip_statuses = {"closed", "awarded", "cancelled", "expired"}

    async with async_session() as db:
        for tender in tenders:
            # Skip tenders that are explicitly closed/awarded
            if tender.status.lower() in skip_statuses:
                skipped += 1
                continue
            # Skip tenders whose deadline has already passed
            if tender.deadline and tender.deadline < now:
                skipped += 1
                continue

            result = await db.execute(
                select(Opportunity).where(
                    Opportunity.source == tender.source,
                    Opportunity.external_id == tender.external_id,
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update fields
                existing.title = tender.title
                existing.description = tender.description or existing.description
                existing.organization = _trunc(tender.organization) or existing.organization
                existing.project_number = _trunc(tender.project_number) or existing.project_number
                existing.published_at = tender.published_at or existing.published_at
                existing.deadline = tender.deadline or existing.deadline
                existing.country = _trunc(tender.country) or existing.country
                existing.sector = _trunc(tender.sector) or existing.sector
                existing.procurement_type = _trunc(tender.procurement_type) or existing.procurement_type
                existing.status = tender.status
                existing.url = tender.url or existing.url
                existing.updated_at = datetime.now(UTC)
                updated += 1
            else:
                opp = Opportunity(
                    source=tender.source,
                    external_id=tender.external_id,
                    url=tender.url,
                    title=tender.title,
                    description=tender.description,
                    organization=_trunc(tender.organization),
                    project_number=_trunc(tender.project_number),
                    published_at=tender.published_at,
                    deadline=tender.deadline,
                    budget_min=tender.budget_min,
                    budget_max=tender.budget_max,
                    currency=tender.currency,
                    location=_trunc(tender.location),
                    country=_trunc(tender.country),
                    sector=_trunc(tender.sector),
                    procurement_type=_trunc(tender.procurement_type),
                    status=tender.status,
                )
                db.add(opp)
                created += 1

        await db.commit()

    return {
        "source": source,
        "total_fetched": len(tenders),
        "created": created,
        "updated": updated,
        "skipped": skipped,
    }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_opportunities(self, source: str, max_pages: int = 5) -> dict:
    """Fetch opportunities from a given source using API/RSS (adb/wb/afdb).

    Runs the async fetcher inside an event loop then upserts results.
    """
    logger.info("Fetching opportunities from %s (max_pages=%d)", source, max_pages)
    try:
        result = asyncio.run(
            _run_fetcher(source, max_pages)
        )
        logger.info("[%s] fetch complete: %s", source, result)
        return result
    except Exception as exc:
        logger.exception("[%s] Fetch failed", source)
        raise self.retry(exc=exc) from exc


@celery_app.task
def fetch_all_sources(max_pages: int = 5) -> list[dict]:
    """Trigger fetch for all configured sources."""
    from app.fetchers import FETCHERS

    results = []
    for source in FETCHERS:
        result = fetch_opportunities.delay(source, max_pages)
        results.append({"source": source, "task_id": result.id})
    return results


async def _cleanup_expired() -> dict:
    """Delete opportunities whose deadline has passed by more than 90 days."""
    from datetime import timedelta
    cutoff = datetime.now(UTC) - timedelta(days=90)
    async with async_session() as db:
        result = await db.execute(
            select(Opportunity).where(
                Opportunity.deadline is not None,
                Opportunity.deadline < cutoff,
            )
        )
        expired = result.scalars().all()
        count = len(expired)
        for opp in expired:
            await db.delete(opp)
        await db.commit()
    return {"deleted": count}


@celery_app.task
def cleanup_expired_opportunities() -> dict:
    """Remove opportunities expired > 90 days. Runs daily at 01:00."""
    logger.info("Cleaning up expired opportunities")
    result = asyncio.run(_cleanup_expired())
    logger.info("Cleanup complete: %s", result)
    return result
