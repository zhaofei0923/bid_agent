"""AfDB (African Development Bank) RSS feed fetcher.

AfDB provides procurement notices via RSS feed:
- Procurement: https://www.afdb.org/en/projects-and-operations/procurement.xml

The feed is standard RSS 2.0 with <item> elements containing
title, link, description, pubDate, and guid.
"""

import logging
import re
from datetime import datetime
from typing import Any
from xml.etree import ElementTree

from app.fetchers.base import BaseFetcher, TenderInfo

logger = logging.getLogger(__name__)

AFDB_RSS_URL = "https://www.afdb.org/en/projects-and-operations/procurement.xml"


class AfDBFetcher(BaseFetcher):
    """Fetcher for AfDB procurement opportunities via RSS feed.

    Parses the AfDB procurement RSS 2.0 feed and normalizes items
    into TenderInfo objects.
    """

    source_name = "afdb"
    base_url = "https://www.afdb.org"
    request_delay: float = 2.0  # Be polite to AfDB servers

    async def fetch_list(self, page: int = 1) -> list[TenderInfo]:
        """Fetch AfDB tender listings from the RSS feed.

        RSS feeds don't support pagination, so all items from the
        feed are returned on page 1. Subsequent pages return [].
        """
        if page > 1:
            return []

        try:
            response = await self._get(AFDB_RSS_URL)
        except Exception:
            logger.exception("[afdb] Failed to fetch RSS feed")
            return []

        return self._parse_feed(response.text)

    async def fetch_detail(self, tender_id: str) -> TenderInfo:
        """Fetch full details for a single AfDB tender.

        AfDB RSS does not provide per-item detail endpoints, so
        this returns a minimal placeholder with the correct URL.
        """
        return TenderInfo(
            source="afdb",
            external_id=tender_id,
            url=f"{self.base_url}/en/documents/procurement/{tender_id}",
            title=f"AfDB Tender {tender_id}",
            status="open",
        )

    # ── Private helpers ───────────────────────────────

    def _parse_feed(self, xml_text: str) -> list[TenderInfo]:
        """Parse the RSS 2.0 XML into a list of TenderInfo."""
        tenders: list[TenderInfo] = []
        try:
            root = ElementTree.fromstring(xml_text)
        except ElementTree.ParseError:
            logger.warning("[afdb] Failed to parse RSS XML")
            return []

        items = root.findall(".//item")
        for item in items:
            try:
                tender = self._parse_item(item)
                if tender:
                    tenders.append(tender)
            except Exception:
                logger.debug("[afdb] Failed to parse RSS item", exc_info=True)

        logger.info("[afdb] Parsed %d items from RSS feed", len(tenders))
        return tenders

    def _parse_item(self, item: Any) -> TenderInfo | None:
        """Parse a single <item> into a TenderInfo."""
        title = _elem_text(item, "title")
        link = _elem_text(item, "link")
        description = _elem_text(item, "description")
        pub_date = _elem_text(item, "pubDate")
        guid = _elem_text(item, "guid")

        if not title:
            return None

        # Derive external_id from guid or link
        external_id = guid or link or ""
        if external_id:
            # Try to extract a numeric/slug id from the URL
            match = re.search(r"/(\d+)(?:[/?#]|$)", external_id)
            if match:
                external_id = match.group(1)
            else:
                external_id = external_id.rstrip("/").split("/")[-1]

        # Clean description (remove HTML tags)
        clean_desc = _strip_html(description)[:2000] if description else ""

        # Extract country / sector hints from description if possible
        country = ""
        sector = ""

        return TenderInfo(
            source="afdb",
            external_id=external_id,
            url=link or f"{self.base_url}/en/procurement",
            title=title.strip(),
            description=clean_desc,
            organization="African Development Bank",
            published_at=_parse_rss_date(pub_date),
            country=country,
            sector=sector,
            procurement_type="Procurement Notice",
            status="open",
        )


# ── Module-level helpers ─────────────────────────────


def _elem_text(parent: Any, tag: str) -> str:
    """Get stripped text from an XML child element."""
    elem = parent.find(tag)
    if elem is None:
        return ""
    return (elem.text or "").strip()


def _parse_rss_date(value: str | None) -> datetime | None:
    """Parse common RSS date string formats."""
    if not value:
        return None

    formats = [
        "%a, %d %b %Y %H:%M:%S %z",    # RFC 822
        "%a, %d %b %Y %H:%M:%S Z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
        "%d %b %Y",
    ]
    cleaned = value.replace("Z", "+0000")
    for fmt in formats:
        try:
            return datetime.strptime(cleaned.strip(), fmt)
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
