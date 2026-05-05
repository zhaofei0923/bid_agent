#!/usr/bin/env python
"""Local script: fetch tender data and export to JSON.

This is intentionally DB-free so it can run on a laptop/office machine and
then upload JSON to the server for import.
"""

import argparse
import asyncio
import dataclasses
import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.fetchers import get_fetcher
from app.fetchers.base import TenderInfo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
)
logger = logging.getLogger("export_tenders")


def _tender_to_dict(tender: TenderInfo) -> dict:
    """Convert TenderInfo dataclass to JSON-serialisable dict."""
    data = dataclasses.asdict(tender)
    for key, value in data.items():
        if isinstance(value, datetime):
            data[key] = value.isoformat()
    return data


def _configure_source_filters(source: str, goods_only: bool) -> None:
    if not goods_only:
        return

    if source == "adb":
        os.environ["ADB_GOODS_ONLY"] = "1"
    elif source == "wb":
        os.environ.setdefault("WB_PROCUREMENT_GROUPS", "GO")
        os.environ.setdefault(
            "WB_NOTICE_TYPES",
            "Invitation for Bids,Invitation for Prequalification",
        )


async def main(args: argparse.Namespace) -> None:
    source = args.source.lower()
    _configure_source_filters(source, args.goods_only)

    output_path = Path(args.output)
    logger.info(
        "Fetching %s data (max_pages=%d, goods_only=%s)...",
        source,
        args.max_pages,
        args.goods_only,
    )

    fetcher = get_fetcher(source)
    async with fetcher:
        tenders = await fetcher.fetch_all(
            max_pages=args.max_pages,
            fetch_details=args.fetch_details,
        )

    logger.info("Fetched %d %s tenders", len(tenders), source.upper())
    if not tenders:
        logger.warning("No tenders fetched — nothing to export")
        sys.exit(1)

    for index, tender in enumerate(tenders[:5], 1):
        logger.info(
            "  #%d  %s | %s | %s | %s",
            index,
            tender.external_id[:30],
            tender.title[:60],
            tender.deadline or "no-deadline",
            tender.status,
        )
    if len(tenders) > 5:
        logger.info("  ... and %d more", len(tenders) - 5)

    data = {
        "source": source,
        "exported_at": datetime.now(UTC).isoformat(),
        "filters": {
            "goods_only": args.goods_only,
        },
        "count": len(tenders),
        "tenders": [_tender_to_dict(tender) for tender in tenders],
    }

    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("Exported %d tenders to %s", len(tenders), output_path.resolve())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export tenders to JSON")
    parser.add_argument(
        "--source",
        "-s",
        choices=("adb", "wb", "afdb"),
        required=True,
        help="Source to fetch locally",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output JSON file path",
    )
    parser.add_argument(
        "--max-pages",
        "-p",
        type=int,
        default=1,
        help="Maximum list pages to fetch",
    )
    parser.add_argument(
        "--fetch-details",
        action="store_true",
        help="Fetch detail pages when the source supports it",
    )
    parser.add_argument(
        "--goods-only",
        action="store_true",
        help="Only export goods/supplies procurement opportunities",
    )
    asyncio.run(main(parser.parse_args()))
