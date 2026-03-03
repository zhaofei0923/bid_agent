#!/usr/bin/env python
"""Local script: fetch ADB data and export to JSON file.

Run this script LOCALLY (your laptop/desktop) where Cloudflare does not
block the IP. The output JSON can then be imported into the remote server DB
using sync_adb.sh.

Usage:
    cd backend
    python -m scripts.export_adb                        # export to adb_export.json
    python -m scripts.export_adb --output /tmp/adb.json # custom output path
    python -m scripts.export_adb --max-pages 5          # limit pages
"""

import argparse
import asyncio
import dataclasses
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.fetchers.adb import ADBFetcher
from app.fetchers.base import TenderInfo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
)
logger = logging.getLogger("export_adb")


def _tender_to_dict(tender: TenderInfo) -> dict:
    """Convert TenderInfo dataclass to JSON-serialisable dict."""
    d = dataclasses.asdict(tender)
    # Convert datetime objects to ISO strings
    for key, val in d.items():
        if isinstance(val, datetime):
            d[key] = val.isoformat()
    return d


async def main(args: argparse.Namespace) -> None:
    output_path = Path(args.output)
    logger.info("Fetching ADB data (max_pages=%d)...", args.max_pages)

    fetcher = ADBFetcher()
    async with fetcher:
        tenders = await fetcher.fetch_all(max_pages=args.max_pages, fetch_details=False)

    logger.info("Fetched %d ADB tenders", len(tenders))

    if not tenders:
        logger.warning("No tenders fetched — nothing to export")
        sys.exit(1)

    # Preview first 5
    for i, t in enumerate(tenders[:5], 1):
        logger.info(
            "  #%d  %s | %s | %s",
            i,
            t.external_id,
            t.title[:60],
            t.status,
        )
    if len(tenders) > 5:
        logger.info("  ... and %d more", len(tenders) - 5)

    data = {
        "source": "adb",
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "count": len(tenders),
        "tenders": [_tender_to_dict(t) for t in tenders],
    }

    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Exported %d tenders to %s", len(tenders), output_path.resolve())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export ADB tenders to JSON (run locally)")
    parser.add_argument(
        "--output", "-o",
        default="adb_export.json",
        help="Output JSON file path (default: adb_export.json)",
    )
    parser.add_argument(
        "--max-pages", "-p",
        type=int,
        default=10,
        help="Maximum RSS pages to fetch (default: 10)",
    )
    args = parser.parse_args()
    asyncio.run(main(args))
