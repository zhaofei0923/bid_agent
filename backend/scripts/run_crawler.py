#!/usr/bin/env python3
"""Standalone crawler runner — no Celery required.

Usage:
    python scripts/run_crawler.py --source adb --max-pages 3
    python scripts/run_crawler.py --source wb --max-pages 2
    python scripts/run_crawler.py --source adb --dry-run   # don't write to DB
"""

import argparse
import asyncio
import logging
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.crawlers.adb import ADBCrawler  # noqa: E402
from app.crawlers.base import BaseCrawler, TenderInfo  # noqa: E402
from app.crawlers.ungm import UNGMCrawler  # noqa: E402
from app.crawlers.wb import WBCrawler  # noqa: E402
from app.database import async_session  # noqa: E402
from app.models.opportunity import Opportunity  # noqa: E402

CRAWLER_MAP: dict[str, type[BaseCrawler]] = {
    "adb": ADBCrawler,
    "wb": WBCrawler,
    "un": UNGMCrawler,
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s - %(message)s",
)
logger = logging.getLogger("run_crawler")


async def upsert_tenders(tenders: list[TenderInfo]) -> dict:
    """Write tenders to database (upsert by source + external_id)."""
    created = 0
    updated = 0

    def _trunc(value: str | None, max_len: int = 100) -> str | None:
        """Truncate a string to fit database column limits."""
        if value and len(value) > max_len:
            return value[: max_len - 3] + "..."
        return value

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

    return {"created": created, "updated": updated}


async def cleanup_expired(source: str | None = None) -> int:
    """Delete opportunities whose deadline has passed or status is closed/archived."""
    from sqlalchemy import or_  # noqa: E402

    now = datetime.now(UTC)
    async with async_session() as db:
        query = select(Opportunity).where(
            or_(
                Opportunity.deadline < now,
                Opportunity.status.in_(["closed", "archived", "awarded"]),
            )
        )
        if source:
            query = query.where(Opportunity.source == source)

        result = await db.execute(query)
        expired = result.scalars().all()
        count = len(expired)
        for opp in expired:
            await db.delete(opp)
        await db.commit()
    return count


async def cleanup_stale(source: str, crawl_start: datetime) -> int:
    """Remove records not refreshed by the latest crawl.

    Any record whose ``updated_at`` is before *crawl_start* no longer
    appears in the active source listing and should be purged.
    """
    from sqlalchemy import or_  # noqa: E402

    async with async_session() as db:
        query = select(Opportunity).where(
            Opportunity.source == source,
            or_(
                Opportunity.updated_at < crawl_start,
                Opportunity.updated_at.is_(None),
            ),
        )
        result = await db.execute(query)
        stale = result.scalars().all()
        count = len(stale)
        for opp in stale:
            await db.delete(opp)
        await db.commit()
    return count


async def main(source: str, max_pages: int, dry_run: bool, cleanup: bool) -> None:
    crawler_cls = CRAWLER_MAP.get(source)
    if not crawler_cls:
        logger.error("Unknown source: %s. Available: %s", source, list(CRAWLER_MAP))
        sys.exit(1)

    # ── Step 1: Clean up expired/closed records ──
    if cleanup:
        removed = await cleanup_expired(source)
        logger.info("Cleanup: removed %d expired/closed %s records", removed, source)

    crawl_start = datetime.now(UTC)
    logger.info("Starting %s crawler (max_pages=%d, dry_run=%s)", source, max_pages, dry_run)

    async with crawler_cls() as crawler:
        tenders = await crawler.crawl_all(max_pages=max_pages, fetch_details=False)

    logger.info("Fetched %d tenders from %s", len(tenders), source)

    if dry_run:
        for t in tenders:
            logger.info(
                "  [%s] %s | %s | %s | deadline=%s",
                t.external_id, t.title[:60], t.country, t.procurement_type, t.deadline,
            )
        logger.info("Dry run — no database writes.")
        return

    if not tenders:
        logger.warning("No tenders fetched, nothing to write.")
        return

    result = await upsert_tenders(tenders)
    logger.info(
        "Done: %d created, %d updated (total fetched: %d)",
        result["created"], result["updated"], len(tenders),
    )

    # ── Step 3: Remove stale records no longer in active listing ──
    if cleanup:
        stale = await cleanup_stale(source, crawl_start)
        if stale:
            logger.info("Stale cleanup: removed %d %s records not in active listing", stale, source)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run opportunity crawler")
    parser.add_argument(
        "--source", required=True, choices=list(CRAWLER_MAP),
        help="Crawler source (adb/wb/un)",
    )
    parser.add_argument(
        "--max-pages", type=int, default=5,
        help="Maximum pages to crawl (default: 5)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print results without writing to database",
    )
    parser.add_argument(
        "--cleanup", action="store_true", default=True,
        help="Remove expired/closed records before crawling (default: True)",
    )
    parser.add_argument(
        "--no-cleanup", dest="cleanup", action="store_false",
        help="Skip expired record cleanup",
    )
    args = parser.parse_args()
    asyncio.run(main(args.source, args.max_pages, args.dry_run, args.cleanup))
