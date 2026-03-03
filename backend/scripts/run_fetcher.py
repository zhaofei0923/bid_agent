#!/usr/bin/env python
"""CLI script to manually trigger API/RSS fetchers for testing.

Usage:
    # Fetch from all sources (default max 5 pages)
    python -m scripts.run_fetcher

    # Fetch from a specific source
    python -m scripts.run_fetcher --source wb
    python -m scripts.run_fetcher --source adb
    python -m scripts.run_fetcher --source afdb

    # Limit pages
    python -m scripts.run_fetcher --source wb --max-pages 2

    # Dry-run: fetch but don't save to DB
    python -m scripts.run_fetcher --source adb --dry-run
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.fetchers import FETCHERS, get_fetcher
from app.fetchers.base import TenderInfo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
)
logger = logging.getLogger("run_fetcher")

VALID_SOURCES = sorted({k for k in FETCHERS if k not in ("worldbank",)})


async def run_fetch(source: str, max_pages: int, dry_run: bool) -> list[TenderInfo]:
    """Run a single fetcher and return results."""
    fetcher = get_fetcher(source)
    logger.info("Fetching from %s (max_pages=%d, dry_run=%s)", source, max_pages, dry_run)

    async with fetcher:
        tenders = await fetcher.fetch_all(max_pages=max_pages, fetch_details=False)

    logger.info("[%s] Fetched %d items", source, len(tenders))

    for i, t in enumerate(tenders[:5], 1):
        logger.info(
            "  #%d  %s | %s | %s | %s",
            i,
            t.external_id[:30],
            t.title[:60],
            t.published_at or "no-date",
            t.url[:80],
        )
    if len(tenders) > 5:
        logger.info("  ... and %d more", len(tenders) - 5)

    if not dry_run:
        await _upsert_to_db(tenders)
    else:
        logger.info("[%s] Dry-run mode — skipping DB upsert", source)

    return tenders


async def _upsert_to_db(tenders: list[TenderInfo]) -> None:
    """Save fetched tenders to the database using the same logic as fetcher_tasks."""
    from datetime import UTC, datetime

    from sqlalchemy import select

    from app.database import async_session
    from app.models.opportunity import Opportunity

    _SKIP_STATUSES = {"closed", "awarded", "cancelled", "expired"}
    created = updated = skipped = 0
    now = datetime.now(UTC)

    def _trunc(value: str | None, max_len: int = 100) -> str | None:
        if value and len(value) > max_len:
            return value[: max_len - 3] + "..."
        return value

    async with async_session() as db:
        for tender in tenders:
            # Skip non-open statuses
            if tender.status.lower() in _SKIP_STATUSES:
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
                existing.title = tender.title
                existing.description = tender.description or existing.description
                existing.url = tender.url or existing.url
                existing.status = tender.status
                existing.updated_at = datetime.now(UTC)
                updated += 1
            else:
                db.add(
                    Opportunity(
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
                )
                created += 1
        await db.commit()

    logger.info("DB upsert: created=%d, updated=%d, skipped=%d", created, updated, skipped)


async def main(args: argparse.Namespace) -> None:
    sources = [args.source] if args.source else VALID_SOURCES
    for source in sources:
        await run_fetch(source, args.max_pages, args.dry_run)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run API/RSS fetchers manually")
    parser.add_argument(
        "--source", "-s",
        choices=VALID_SOURCES,
        default=None,
        help="Source to fetch from (default: all)",
    )
    parser.add_argument(
        "--max-pages", "-p",
        type=int,
        default=5,
        help="Maximum pages to fetch (default: 5)",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Fetch but don't save to database",
    )

    args = parser.parse_args()
    asyncio.run(main(args))
