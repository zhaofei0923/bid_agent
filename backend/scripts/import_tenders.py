#!/usr/bin/env python
"""Server-side script: import tenders from JSON file into the database.

This script runs INSIDE the Docker container on the remote server.
It reads a JSON file produced by scripts/export_tenders.py and upserts the
tenders into the Opportunity table.

Usage (called automatically by sync_adb.sh):
    docker exec bidagent-backend python -m scripts.import_tenders /tmp/adb_export.json

Or manually:
    docker exec bidagent-backend python -m scripts.import_tenders /app/data/adb_export.json
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
)
logger = logging.getLogger("import_tenders")

_SKIP_STATUSES = {"closed", "awarded", "cancelled", "expired"}


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except (ValueError, TypeError):
        return None


def _trunc(value: str | None, max_len: int = 100) -> str | None:
    if value and len(value) > max_len:
        return value[: max_len - 3] + "..."
    return value


async def import_tenders(json_path: Path, clear_existing: bool) -> None:
    from sqlalchemy import delete, select

    from app.database import async_session
    from app.models.opportunity import Opportunity

    data = json.loads(json_path.read_text(encoding="utf-8"))
    tenders = data.get("tenders", [])
    source = data.get("source", "adb")
    exported_at = data.get("exported_at", "unknown")
    goods_only = bool(data.get("filters", {}).get("goods_only"))

    logger.info(
        "Importing %d %s tenders (exported at %s)",
        len(tenders), source, exported_at,
    )

    now = datetime.now(UTC)
    created = updated = skipped = 0
    deleted_invalid = deleted_expired = deleted_non_goods = deleted_missing = 0
    incoming_ids = {
        str(item.get("external_id"))
        for item in tenders
        if item.get("external_id")
    }

    async with async_session() as db:
        if clear_existing:
            result = await db.execute(
                delete(Opportunity).where(Opportunity.source == source)
            )
            logger.info("Cleared %d existing %s records", result.rowcount, source)

        for item in tenders:
            status = (item.get("status") or "open").lower()
            deadline = _parse_dt(item.get("deadline"))
            ext_id = item.get("external_id", "")
            if not ext_id:
                skipped += 1
                continue

            result = await db.execute(
                select(Opportunity).where(
                    Opportunity.source == source,
                    Opportunity.external_id == ext_id,
                )
            )
            existing = result.scalar_one_or_none()

            if status in _SKIP_STATUSES or (deadline and deadline < now):
                if existing:
                    await db.delete(existing)
                    deleted_invalid += 1
                else:
                    skipped += 1
                continue

            if existing:
                existing.title = item.get("title") or existing.title
                existing.description = item.get("description") or existing.description
                existing.url = item.get("url") or existing.url
                existing.organization = (
                    _trunc(item.get("organization")) or existing.organization
                )
                existing.project_number = (
                    _trunc(item.get("project_number")) or existing.project_number
                )
                existing.published_at = (
                    _parse_dt(item.get("published_at")) or existing.published_at
                )
                existing.deadline = deadline or existing.deadline
                existing.budget_min = item.get("budget_min") or existing.budget_min
                existing.budget_max = item.get("budget_max") or existing.budget_max
                existing.currency = item.get("currency") or existing.currency
                existing.location = _trunc(item.get("location")) or existing.location
                existing.country = _trunc(item.get("country")) or existing.country
                existing.sector = _trunc(item.get("sector")) or existing.sector
                existing.procurement_type = (
                    _trunc(item.get("procurement_type")) or existing.procurement_type
                )
                existing.status = status
                existing.updated_at = now
                updated += 1
            else:
                db.add(Opportunity(
                    source=source,
                    external_id=ext_id,
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    organization=_trunc(item.get("organization")),
                    project_number=_trunc(item.get("project_number")),
                    published_at=_parse_dt(item.get("published_at")),
                    deadline=deadline,
                    budget_min=item.get("budget_min"),
                    budget_max=item.get("budget_max"),
                    currency=item.get("currency", "USD"),
                    location=_trunc(item.get("location")),
                    country=_trunc(item.get("country")),
                    sector=_trunc(item.get("sector")),
                    procurement_type=_trunc(item.get("procurement_type")),
                    status=status,
                ))
                created += 1

        result = await db.execute(
            delete(Opportunity).where(
                Opportunity.source == source,
                Opportunity.deadline.is_not(None),
                Opportunity.deadline < now,
            )
        )
        deleted_expired += result.rowcount or 0
        result = await db.execute(
            delete(Opportunity).where(
                Opportunity.source == source,
                Opportunity.status.in_(_SKIP_STATUSES),
            )
        )
        deleted_expired += result.rowcount or 0
        if goods_only:
            goods_condition = (
                Opportunity.procurement_type.ilike("%goods%")
                | (Opportunity.sector == "Goods")
            )
            result = await db.execute(
                delete(Opportunity).where(
                    Opportunity.source == source,
                    ~goods_condition,
                )
            )
            deleted_non_goods = result.rowcount or 0
        if incoming_ids:
            result = await db.execute(
                delete(Opportunity).where(
                    Opportunity.source == source,
                    Opportunity.external_id.not_in(incoming_ids),
                )
            )
            deleted_missing = result.rowcount or 0
        await db.commit()

    logger.info(
        "Import complete: created=%d, updated=%d, skipped=%d, "
        "deleted_invalid=%d, deleted_expired=%d, deleted_non_goods=%d, "
        "deleted_missing=%d",
        created,
        updated,
        skipped,
        deleted_invalid,
        deleted_expired,
        deleted_non_goods,
        deleted_missing,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import tenders JSON into DB (run in Docker)")
    parser.add_argument(
        "json_file",
        help="Path to the JSON file produced by export_adb.py",
    )
    parser.add_argument(
        "--clear", "-c",
        action="store_true",
        help="Clear existing records for this source before importing",
    )
    args = parser.parse_args()

    json_path = Path(args.json_file)
    if not json_path.exists():
        logger.error("File not found: %s", json_path)
        sys.exit(1)

    asyncio.run(import_tenders(json_path, clear_existing=args.clear))
