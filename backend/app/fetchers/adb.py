"""ADB (Asian Development Bank) RSS feed fetcher.

ADB provides procurement data through its official RSS feeds:
- Invitation for Bids:         https://www.adb.org/rss/tenders/all/all/1521%201521/all/1576/all
- Advanced Notices:            https://www.adb.org/rss/tenders/all/all/1536/all/all/all
- Consulting Services (CSRN):  https://www.adb.org/rss/tenders/all/all/1566%201516/all/1576/all
- Prequalification:            https://www.adb.org/rss/tenders/all/all/1611/all/all/all

Note: These are the original ADB RSS URLs discovered from FeedBurner source tags.
FeedBurner URLs (feeds.feedburner.com) are blocked by GFW on mainland China servers.
The direct ADB URLs include full <category> metadata: Date, Project Number, Status,
Countries, Sectors — enabling proper status-based filtering.
"""

import logging
import os
import re
from datetime import datetime
from typing import Any
from xml.etree import ElementTree

import httpx

from app.fetchers.base import BaseFetcher, TenderInfo

logger = logging.getLogger(__name__)

# ADB direct RSS URLs — discovered from FeedBurner <source> tags.
# These bypass FeedBurner (blocked by GFW on CN servers) and include
# full <category> metadata with Status, Date, Countries, Sectors.
# 'contracts_awarded' is intentionally excluded: those items have
# Status=Awarded (already signed), so they are NOT open opportunities.
# 'consulting_services' is intentionally excluded: the platform only
# tracks Goods/Works procurement opportunities, not consulting engagements.
ADB_RSS_FEEDS = {
    "invitation_for_bids": "https://www.adb.org/rss/tenders/all/all/1521%201521/all/1576/all",
    "advanced_notices": "https://www.adb.org/rss/tenders/all/all/1536/all/all/all",
    "prequalification": "https://www.adb.org/rss/tenders/all/all/1611/all/all/all",
}

# Fallback feed: always accessible but provides title+link only (no status metadata).
# Items from this feed are accepted as-is (assumed active) since the feed
# itself only lists active notices.
_FALLBACK_FEED_URL = "https://www.adb.org/rss/procurement-notices"
_FALLBACK_FEED_NAME = "procurement_notices"

# Statuses considered "open" / worth tracking
_ACTIVE_STATUSES = {"active", "open"}


class ADBFetcher(BaseFetcher):
    """Fetcher for ADB procurement opportunities via RSS feeds."""

    source_name = "adb"
    base_url = "https://www.adb.org"

    # Primary feed for active tenders
    _default_feed = ADB_RSS_FEEDS["invitation_for_bids"]

    def __init__(self) -> None:
        super().__init__()
        # Extend headers with Cloudflare-friendly browser signals
        self._headers.update({
            "Referer": "https://www.adb.org/",
            "Accept-Encoding": "gzip, deflate",  # no 'br': brotli needs extra package
            "sec-ch-ua": '"Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
        })
        # Optional proxy for bypassing Cloudflare WAF on CN servers.
        # Set ADB_PROXY_URL=http://<singapore-server-ip>:3128 in .env
        self._proxy_url: str | None = os.getenv("ADB_PROXY_URL")

    async def __aenter__(self):
        proxy_url = self._proxy_url
        if proxy_url:
            logger.info("[adb] Using proxy: %s", proxy_url)
        self.client = httpx.AsyncClient(
            timeout=30,
            headers=self._headers,
            follow_redirects=True,
            proxy=proxy_url,
        )
        return self

    async def fetch_list(self, page: int = 1) -> list[TenderInfo]:
        """Fetch ADB tender listings from RSS feeds.

        Tries the categorised tenders feeds first (full metadata + status filter).
        Falls back to the aggregated procurement-notices feed if all tenders
        feeds return 403 (Cloudflare WAF blocks CN server IPs for /rss/tenders/).
        Items from the fallback feed have no category metadata and are accepted
        as active (the feed only lists open notices by design).

        ADB RSS feeds return ALL active tenders in a single request (no
        pagination). Only page 1 is meaningful; subsequent pages return [].
        """
        # RSS feeds have no pagination — all active items arrive in page 1.
        if page > 1:
            return []

        tenders: list[TenderInfo] = []
        any_success = False

        # Fetch from multiple feeds to get comprehensive data
        for feed_name, feed_url in ADB_RSS_FEEDS.items():
            try:
                items = await self._fetch_rss_feed(feed_url, feed_name)
                tenders.extend(items)
                any_success = True
            except Exception:
                logger.warning("[adb] Failed to fetch feed: %s", feed_name)

        # All tenders feeds failed (e.g. Cloudflare 403 on CN server IPs)
        # — fall back to the always-accessible procurement-notices aggregated feed.
        if not any_success:
            logger.warning(
                "[adb] All tenders feeds failed, falling back to %s",
                _FALLBACK_FEED_URL,
            )
            try:
                items = await self._fetch_rss_feed(
                    _FALLBACK_FEED_URL, _FALLBACK_FEED_NAME
                )
                tenders.extend(items)
            except Exception:
                logger.error("[adb] Fallback feed also failed: %s", _FALLBACK_FEED_URL)

        # Remove duplicates by external_id
        seen: set[str] = set()
        unique_tenders: list[TenderInfo] = []
        for tender in tenders:
            if tender.external_id not in seen:
                seen.add(tender.external_id)
                unique_tenders.append(tender)

        logger.info("[adb] Total unique tenders: %d", len(unique_tenders))
        return unique_tenders

    async def fetch_detail(self, tender_id: str) -> TenderInfo:
        """Fetch full details for a single ADB tender.

        Since RSS feeds don't provide full details, this returns
        the basic tender info with an enriched URL.
        """
        url = f"{self.base_url}/node/{tender_id}"
        return TenderInfo(
            source="adb",
            external_id=tender_id,
            url=url,
            title=f"ADB Tender {tender_id}",
            status="open",
        )

    async def _fetch_rss_feed(self, feed_url: str, feed_name: str) -> list[TenderInfo]:
        """Fetch and parse an RSS feed."""
        response = await self._get(feed_url)
        content = response.text

        tenders: list[TenderInfo] = []

        try:
            # Parse XML
            root = ElementTree.fromstring(content)

            # Handle RSS 2.0
            items = root.findall(".//item")
            if not items:
                # Handle Atom
                items = root.findall(".//entry")

            for item in items:
                try:
                    tender = self._parse_rss_item(item, feed_name)
                    if tender:
                        tenders.append(tender)
                except Exception:
                    logger.debug("[adb] Failed to parse RSS item")
                    continue

            logger.info("[adb] Feed %s: parsed %d items", feed_name, len(tenders))

        except ElementTree.ParseError:
            logger.warning("[adb] Failed to parse RSS feed: %s", feed_name)

        return tenders

    def _parse_rss_item(self, item: Any, feed_name: str) -> TenderInfo | None:
        """Parse a single RSS/Atom item into TenderInfo."""

        # Try RSS 2.0 format
        title = self._get_element_text(item, "title")
        link = self._get_element_text(item, "link")
        description = self._get_element_text(item, "description")
        pub_date = self._get_element_text(item, "pubDate")

        # Try Atom format
        if not title:
            title = self._get_element_text(item, "title")
        if not link:
            # Atom links can be in href attribute
            link_elem = item.find("link")
            if link_elem is not None and link_elem.get("href"):
                link = link_elem.get("href")
        if not description:
            summary = self._get_element_text(item, "summary")
            content = self._get_element_text(item, "content")
            description = summary or content or ""

        if not title:
            return None

        # Extract external_id from link (e.g., /node/123456)
        external_id = ""
        if link:
            match = re.search(r"/node/(\d+)", link)
            # Use the link as ID if no node ID is found.
            external_id = (
                match.group(1) if match else link.rstrip("/").split("/")[-1]
            )

        # Determine procurement type from feed name
        procurement_type = _map_feed_to_procurement_type(feed_name)

        # Skip consulting-type items even if they appear in the fallback feed
        if _is_consulting_type(procurement_type, title):
            return None

        # Parse <category> field: "Date: 2026-03-02|Project Number: 59312-001|Status: Active|Countries: India|Sectors: ..."
        category_text = self._get_element_text(item, "category")
        cat = _parse_category(category_text)

        status_raw = cat.get("status", "active").lower()
        if status_raw not in _ACTIVE_STATUSES:
            # Skip awarded, closed, expired, etc.
            return None

        status = "open"
        country = cat.get("countries", "")
        sector = cat.get("sectors", "")
        project_number = cat.get("project number", "")

        # Parse publication date: prefer RSS <pubDate>, fall back to category "Date:" field
        published_at = _parse_rss_date(pub_date) or _parse_rss_date(cat.get("date", ""))

        # Clean description (remove HTML)
        description = _strip_html(description)[:2000] if description else ""

        return TenderInfo(
            source="adb",
            external_id=external_id,
            url=link or f"{self.base_url}/node/{external_id}",
            title=title.strip(),
            description=description,
            procurement_type=procurement_type,
            published_at=published_at,
            country=country,
            sector=sector,
            project_number=project_number,
            status=status,
        )

    def _get_element_text(self, parent: Any, tag: str) -> str:
        """Get text content from an XML element."""
        elem = parent.find(tag)
        if elem is None:
            return ""
        text = elem.text
        return text.strip() if text else ""


def _map_feed_to_procurement_type(feed_name: str) -> str:
    """Map RSS feed name to procurement type."""
    mapping = {
        "procurement_notices": "Procurement Notice",
        "invitation_for_bids": "Invitation for Bids",
        "advanced_notices": "Advanced Notice",
        "consulting_services": "Consulting Services",
        "prequalification": "Invitation for Prequalification",
    }
    return mapping.get(feed_name, feed_name)


# Keywords that indicate a consulting-type notice (to be excluded).
_CONSULTING_KEYWORDS = (
    "consulting",
    "consultant",
    "expression of interest",
    "eoi",
    "individual consultant",
    "国际咨询",
    "咨询服务",
)


def _is_consulting_type(procurement_type: str, title: str) -> bool:
    """Return True if the item is a consulting-type notice that should be skipped."""
    pt_lower = procurement_type.lower()
    title_lower = title.lower()
    return any(kw in pt_lower or kw in title_lower for kw in _CONSULTING_KEYWORDS)


def _parse_category(text: str) -> dict[str, str]:
    """Parse ADB <category> pipe-delimited key-value string.

    Example input:
        'Date: 2026-03-02|Project Number: 59312-001|Status: Active|Countries: India|Sectors: Transport'
    """
    result: dict[str, str] = {}
    if not text:
        return result
    for part in text.split("|"):
        part = part.strip()
        if ":" in part:
            key, _, value = part.partition(":")
            result[key.strip().lower()] = value.strip()
    return result


def _parse_rss_date(value: str | None) -> datetime | None:
    """Parse RSS/Atom date formats."""
    if not value:
        return None

    # Common RSS date formats
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",    # RFC 822: "Mon, 01 Jan 2024 12:00:00 +0000"
        "%a, %d %b %Y %H:%M:%S Z",     # RFC 822 with Z
        "%Y-%m-%dT%H:%M:%SZ",          # ISO 8601
        "%Y-%m-%dT%H:%M:%S%z",         # ISO 8601 with timezone
        "%Y-%m-%d",                     # Simple date
        "%d %b %Y",                     # "01 Jan 2024"
    ]

    # Try to parse with each format
    for fmt in formats:
        try:
            # Handle 'Z' as UTC
            value = value.replace("Z", "+0000")
            return datetime.strptime(value.strip(), fmt)
        except (ValueError, TypeError):
            continue

    return None


def _strip_html(html: str | None) -> str:
    """Remove HTML tags and collapse whitespace."""
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&[a-z]+;", " ", text)
    return re.sub(r"\s+", " ", text).strip()
