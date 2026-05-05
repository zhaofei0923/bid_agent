"""World Bank procurement API fetcher.

Uses the official World Bank Procurement API v2.
API documentation: https://search.worldbank.org/api/v2/procnotices
"""

import asyncio
import logging
import os
import re
from datetime import UTC, datetime, time

from app.fetchers.base import BaseFetcher, TenderInfo

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


# Notice types that represent open procurement opportunities.
# 'Contract Award' is excluded — those are already-signed contracts, not open bids.
_OPEN_NOTICE_TYPES = {
    "Invitation for Bids",
    "Invitation for Prequalification",
    "Request for Proposals",
    "Request for Expression of Interest",
    "Request for Quotation",
    "General Procurement Notice",
    "Specific Procurement Notice",
}

_DEFAULT_ROWS = int(os.getenv("WB_ROWS", "500"))


def _csv_env(name: str) -> list[str]:
    value = os.getenv(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]


class WorldBankFetcher(BaseFetcher):
    """Fetcher for World Bank procurement/consulting opportunities."""

    source_name = "wb"
    base_url = "https://www.worldbank.org"

    # World Bank procurement API
    _api_url = "https://search.worldbank.org/api/v2/procnotices"

    async def fetch_list(self, page: int = 1) -> list[TenderInfo]:
        """Fetch World Bank procurement notices.

        The API is filtered by deadline_strdate so only currently-valid
        notices are returned upstream. Optional environment filters:
        WB_PROCUREMENT_GROUPS=GO and WB_NOTICE_TYPES=Invitation for Bids,...

        Contract Award notices are excluded — those are completed contracts,
        not open procurement opportunities.
        """
        today = datetime.now(UTC).date().isoformat()
        procurement_groups = _csv_env("WB_PROCUREMENT_GROUPS")
        notice_types = _csv_env("WB_NOTICE_TYPES") or sorted(_OPEN_NOTICE_TYPES)
        goods_only = {group.upper() for group in procurement_groups} == {"GO"}

        params = {
            "format": "json",
            "rows": _DEFAULT_ROWS,
            "os": (page - 1) * _DEFAULT_ROWS,  # offset
            "srt": os.getenv("WB_SORT_BY", "noticedate"),
            "order": os.getenv("WB_SORT_ORDER", "desc"),
            "apilang": "en",
            "srce": "both",
            "deadline_strdate": today,
            "notice_type_exact": "^".join(notice_types),
        }
        if procurement_groups:
            params["procurement_group_exact"] = "^".join(procurement_groups)

        for attempt in range(1, 4):
            try:
                response = await self._get(self._api_url, params=params)
                data = response.json()
                break
            except Exception:
                if attempt == 3:
                    logger.exception("[wb] Failed to fetch list page %d", page)
                    return []
                logger.warning(
                    "[wb] Fetch page %d failed (attempt %d/3), retrying",
                    page,
                    attempt,
                )
                await asyncio.sleep(attempt * 2)

        items = data.get("procnotices", {})
        if isinstance(items, dict):
            items = list(items.values())
        elif not isinstance(items, list):
            items = []

        now = datetime.now(UTC)
        tenders: list[TenderInfo] = []
        expired_count = 0
        non_open_count = 0

        for item in items:
            try:
                notice_type = item.get("notice_type", "")

                # Skip Contract Award and other non-open types
                if _OPEN_NOTICE_TYPES and notice_type not in _OPEN_NOTICE_TYPES:
                    non_open_count += 1
                    continue
                if goods_only and _looks_consulting_notice(item):
                    non_open_count += 1
                    continue

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

        if non_open_count:
            logger.debug(
                "[wb] Page %d: skipped %d contract-award/non-open items",
                page,
                non_open_count,
            )
        if expired_count:
            logger.info(
                "[wb] Page %d: skipped %d expired items",
                page, expired_count,
            )

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
        deadline=_parse_wb_deadline(item),
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


def _looks_consulting_notice(item: dict) -> bool:
    text = " ".join(
        str(item.get(key) or "")
        for key in ("bid_description", "project_name", "notice_text", "notice_type")
    ).lower()
    consulting_terms = (
        "consulting services",
        "consultancy",
        "consultant",
        "expression of interest",
        "expressions of interest",
    )
    return any(term in text for term in consulting_terms)


def _parse_wb_deadline(item: dict) -> datetime | None:
    """Parse WB deadline date plus optional local-time field.

    The API exposes the time without timezone. Treat it as UTC rather than
    midnight so notices are not incorrectly expired at the start of deadline day.
    """
    dt = _parse_wb_date(
        item.get("submission_deadline_date") or item.get("submission_date")
    )
    if not dt:
        return None

    time_text = (item.get("submission_deadline_time") or "").strip()
    if time_text:
        for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p"):
            try:
                parsed_time = datetime.strptime(time_text, fmt).time()
                return datetime.combine(dt.date(), parsed_time, tzinfo=UTC)
            except ValueError:
                continue

    return datetime.combine(dt.date(), time.max, tzinfo=UTC)


def _parse_wb_date(value: str | None) -> datetime | None:
    """Parse World Bank date formats.

    Always returns a timezone-aware (UTC) datetime so comparisons with
    ``datetime.now(UTC)`` work correctly.
    """
    if not value:
        return None

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
                dt = dt.replace(tzinfo=UTC)
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
