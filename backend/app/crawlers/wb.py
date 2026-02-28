"""WB (World Bank) opportunity crawler.

Scrapes consulting/procurement opportunities from worldbank.org.
Uses the official World Bank Procurement API v2.
"""

import logging
import re
from datetime import UTC, datetime

from app.crawlers.base import BaseCrawler, TenderInfo

logger = logging.getLogger(__name__)

# Map procurement_group codes to human-readable sector labels
_PROCUREMENT_GROUP_MAP: dict[str, str] = {
    "GO": "Goods",
    "WK": "Works",
    "CW": "Civil Works",
    "CS": "Consulting Services",
    "NC": "Non-Consulting Services",
}


def _build_notice_url(notice_id: str) -> str:
    """Construct the public URL for a WB procurement notice."""
    return (
        f"https://projects.worldbank.org/en/projects-operations/"
        f"procurement-detail/{notice_id}"
    )


def _strip_html(html: str | None) -> str:
    """Remove HTML tags and collapse whitespace."""
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&\w+;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


class WBCrawler(BaseCrawler):
    """Crawler for World Bank procurement/consulting opportunities."""

    source_name = "wb"
    base_url = "https://www.worldbank.org"

    # World Bank procurement API
    _api_url = "https://search.worldbank.org/api/v2/procnotices"

    async def fetch_list(self, page: int = 1) -> list[TenderInfo]:
        """Fetch World Bank procurement notices.

        Only returns tenders whose submission deadline is in the future.
        When an entire page contains only expired items the crawler
        returns an empty list, which signals `crawl_all()` to stop.
        """
        params = {
            "format": "json",
            "rows": 20,
            "os": (page - 1) * 20,  # offset
            "srt": "noticedate",
            "order": "desc",
        }

        try:
            response = await self._get(self._api_url, params=params)
            data = response.json()
        except Exception:
            logger.exception("[wb] Failed to fetch list page %d", page)
            return []

        items = data.get("procnotices", {})
        if isinstance(items, dict):
            items = list(items.values())
        elif not isinstance(items, list):
            items = []

        now = datetime.now(UTC)
        tenders: list[TenderInfo] = []
        expired_count = 0

        for item in items:
            try:
                tender = _parse_item(item)
                if not tender:
                    continue
                # Skip records whose deadline has already passed
                if tender.deadline and tender.deadline < now:
                    expired_count += 1
                    continue
                tenders.append(tender)
            except Exception:
                logger.warning("[wb] Failed to parse item: %s", item.get("id"))
                continue

        if expired_count:
            logger.info(
                "[wb] Page %d: skipped %d expired items",
                page, expired_count,
            )

        # If every item on the page was expired, signal end-of-data
        if items and not tenders:
            logger.info(
                "[wb] Page %d: all %d items expired, stopping",
                page, len(items),
            )
            return []

        return tenders

    async def fetch_detail(self, tender_id: str) -> TenderInfo:
        """Fetch full details for a World Bank notice."""
        params = {"format": "json", "id": tender_id}

        response = await self._get(self._api_url, params=params)
        data = response.json()

        items = data.get("procnotices", {})
        if isinstance(items, dict):
            items = list(items.values())

        if not items:
            raise ValueError(f"No WB notice found for ID {tender_id}")

        tender = _parse_item(items[0], tender_id=tender_id)
        if not tender:
            raise ValueError(f"Failed to parse WB notice {tender_id}")
        return tender


def _parse_item(item: dict, *, tender_id: str | None = None) -> TenderInfo | None:
    """Convert a single WB API record to TenderInfo."""
    ext_id = str(item.get("id", tender_id or ""))
    if not ext_id:
        return None

    # Use bid_description as primary title; fall back to project_name
    title = item.get("bid_description") or item.get("project_name") or ""

    # Strip HTML from notice_text for description
    description = _strip_html(item.get("notice_text"))

    country = item.get("project_ctry_name", "")
    sector = _PROCUREMENT_GROUP_MAP.get(
        item.get("procurement_group", ""), item.get("procurement_group", "")
    )
    procurement_type = (
        item.get("procurement_method_name")
        or item.get("notice_type")
        or ""
    )
    organization = item.get("contact_organization") or item.get("borrower", "")

    return TenderInfo(
        source="wb",
        external_id=ext_id,
        url=_build_notice_url(ext_id),
        title=title,
        description=description,
        organization=organization,
        project_number=item.get("project_id"),
        published_at=_parse_wb_date(item.get("noticedate")),
        deadline=_parse_wb_date(
            item.get("submission_deadline_date") or item.get("submission_date")
        ),
        budget_min=_parse_float(item.get("estimated_cost")),
        budget_max=_parse_float(item.get("estimated_cost")),
        currency=item.get("currency", "USD"),
        location=country,
        country=country,
        sector=sector,
        procurement_type=procurement_type,
        status="open",
        raw_data=item,
    )


def _parse_wb_date(value: str | None) -> datetime | None:
    """Parse World Bank date formats.

    Always returns a timezone-aware (UTC) datetime so comparisons with
    ``datetime.now(UTC)`` work correctly.
    """
    if not value:
        return None
    from datetime import timezone

    for fmt in (
        "%Y-%m-%dT%H:%M:%SZ",
        "%d-%b-%Y",       # e.g. 19-Feb-2026
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d-%B-%Y",       # e.g. 19-February-2026
    ):
        try:
            dt = datetime.strptime(value, fmt)
            # Ensure the result is always UTC-aware
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            continue
    return None


def _parse_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return None
