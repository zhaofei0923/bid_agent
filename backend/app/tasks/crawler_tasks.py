"""Crawler tasks — periodic opportunity fetching via Celery."""

import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import select

from app.crawlers.adb import ADBCrawler
from app.crawlers.base import BaseCrawler, TenderInfo
from app.crawlers.ungm import UNGMCrawler
from app.crawlers.wb import WBCrawler
from app.database import async_session
from app.models.opportunity import Opportunity
from app.tasks import celery_app

logger = logging.getLogger(__name__)

CRAWLER_MAP: dict[str, type[BaseCrawler]] = {
    "adb": ADBCrawler,
    "wb": WBCrawler,
    "un": UNGMCrawler,
}


async def _run_crawler(source: str, max_pages: int = 5) -> dict:
    """Async implementation: crawl and upsert opportunities."""
    crawler_cls = CRAWLER_MAP.get(source)
    if not crawler_cls:
        raise ValueError(f"Unknown crawler source: {source}")

    def _trunc(value: str | None, max_len: int = 100) -> str | None:
        """Truncate a string to fit database column limits."""
        if value and len(value) > max_len:
            return value[: max_len - 3] + "..."
        return value

    tenders: list[TenderInfo] = []
    async with crawler_cls() as crawler:
        tenders = await crawler.crawl_all(max_pages=max_pages, fetch_details=False)

    created = 0
    updated = 0

    async with async_session() as db:
        for tender in tenders:
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
    }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def crawl_opportunities(self, source: str, max_pages: int = 5) -> dict:
    """Crawl opportunities from a given source (adb/wb/un).

    Runs the async crawler inside an event loop then upserts results.
    """
    logger.info("Crawling opportunities from %s (max_pages=%d)", source, max_pages)
    try:
        result = asyncio.run(
            _run_crawler(source, max_pages)
        )
        logger.info("[%s] crawl complete: %s", source, result)
        return result
    except Exception as exc:
        logger.exception("[%s] Crawl failed", source)
        raise self.retry(exc=exc) from exc


@celery_app.task
def crawl_all_sources(max_pages: int = 5) -> list[dict]:
    """Trigger crawl for all configured sources."""
    results = []
    for source in CRAWLER_MAP:
        result = crawl_opportunities.delay(source, max_pages)
        results.append({"source": source, "task_id": result.id})
    return results
