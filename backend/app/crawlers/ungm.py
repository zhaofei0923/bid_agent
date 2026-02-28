"""UNGM (United Nations Global Marketplace) opportunity crawler.

Scrapes UN procurement opportunities from ungm.org.
"""

import logging
from datetime import datetime

from app.crawlers.base import BaseCrawler, TenderInfo

logger = logging.getLogger(__name__)


class UNGMCrawler(BaseCrawler):
    """Crawler for UNGM procurement opportunities."""

    source_name = "un"
    base_url = "https://www.ungm.org"

    _search_url = "https://www.ungm.org/Public/Notice"
    _detail_url = "https://www.ungm.org/Public/Notice"

    async def fetch_list(self, page: int = 1) -> list[TenderInfo]:
        """Fetch UNGM notice listing page.

        Note: UNGM pages are server-rendered HTML. This implementation
        uses the public search endpoint. A more robust version would
        use Cloudflare bypass if needed.
        """
        params = {
            "PageIndex": page,
            "PageSize": 20,
            "SortField": "DatePublished",
            "SortAscending": "false",
        }

        try:
            response = await self._get(self._search_url, params=params)
            # UNGM may return HTML or JSON depending on headers
            content_type = response.headers.get("content-type", "")

            if "json" in content_type:
                return self._parse_json_list(response.json())
            else:
                return self._parse_html_list(response.text)
        except Exception:
            logger.exception("[un] Failed to fetch list page %d", page)
            return []

    async def fetch_detail(self, tender_id: str) -> TenderInfo:
        """Fetch full details for a UNGM notice."""
        detail_url = f"{self._detail_url}/{tender_id}"

        response = await self._get(detail_url)
        data = response.text

        # Basic HTML parsing fallback
        return TenderInfo(
            source="un",
            external_id=tender_id,
            url=detail_url,
            title=f"UNGM Notice {tender_id}",
            description=data[:500] if data else "",
            status="open",
        )

    def _parse_json_list(self, data: dict | list) -> list[TenderInfo]:
        """Parse JSON response from UNGM API."""
        items = data if isinstance(data, list) else data.get("Results", [])

        tenders: list[TenderInfo] = []
        for item in items:
            try:
                tender = TenderInfo(
                    source="un",
                    external_id=str(item.get("ID", item.get("Reference", ""))),
                    url=f"{self.base_url}/Public/Notice/{item.get('ID', '')}",
                    title=item.get("Title", ""),
                    description=item.get("Description", ""),
                    organization=item.get("AgencyName", ""),
                    published_at=_parse_ungm_date(item.get("DatePublished")),
                    deadline=_parse_ungm_date(item.get("Deadline")),
                    country=item.get("Country", ""),
                    sector=item.get("UNSPSCDescription", ""),
                    procurement_type=item.get("SolicitationType", ""),
                    status="open",
                    raw_data=item,
                )
                tenders.append(tender)
            except Exception:
                logger.warning("[un] Failed to parse item")
                continue

        return tenders

    def _parse_html_list(self, html: str) -> list[TenderInfo]:
        """Fallback HTML parsing for UNGM listings.

        A production implementation would use BeautifulSoup or lxml.
        This placeholder extracts minimal data.
        """
        # TODO: Implement proper HTML parsing with BeautifulSoup
        logger.warning("[un] HTML parsing not fully implemented, returning empty")
        return []


def _parse_ungm_date(value: str | None) -> datetime | None:
    """Parse UNGM date formats."""
    if not value:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d",
        "%d-%b-%Y",
    ):
        try:
            return datetime.strptime(value.split("+")[0].split("Z")[0], fmt)
        except (ValueError, TypeError):
            continue
    return None
