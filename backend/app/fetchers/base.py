"""BaseFetcher — abstract base class for all API/RSS fetchers.

All fetchers inherit from this class, implementing
`fetch_list()` and `fetch_detail()`.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import httpx

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


@dataclass
class TenderInfo:
    """Normalized tender/opportunity data from any source."""

    source: str                          # adb / wb / afdb
    external_id: str                     # Source-specific ID
    url: str
    title: str
    description: str = ""
    organization: str = ""
    project_number: str | None = None
    published_at: datetime | None = None
    deadline: datetime | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    currency: str = "USD"
    location: str = ""
    country: str = ""
    sector: str = ""
    procurement_type: str = ""
    status: str = "open"
    raw_data: dict[str, Any] = field(default_factory=dict)


class BaseFetcher(ABC):
    """Abstract base for all API/RSS based fetchers.

    Fetchers use official APIs or RSS feeds to retrieve
    procurement opportunities from ADB, WB, and AfDB.
    """

    source_name: str = ""
    base_url: str = ""
    request_delay: float = 1.0  # Default 1 second between requests

    def __init__(self) -> None:
        self.client: httpx.AsyncClient | None = None
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "application/json, application/rss+xml, text/xml, */*",
        }

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout=30,
            headers=self._headers,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    # ── Abstract methods ──────────────────────────────

    @abstractmethod
    async def fetch_list(self, page: int = 1) -> list[TenderInfo]:
        """Fetch a page of tender listings from the source.

        Args:
            page: 1-based page number.

        Returns:
            List of TenderInfo objects with at least external_id, url, title.
        """

    @abstractmethod
    async def fetch_detail(self, tender_id: str) -> TenderInfo:
        """Fetch full details for a single tender.

        Args:
            tender_id: Source-specific tender identifier.

        Returns:
            TenderInfo with all available fields populated.
        """

    # ── Utility methods ───────────────────────────────

    async def _get(self, url: str, **kwargs) -> httpx.Response:
        """Perform a GET request with rate limiting."""
        if not self.client:
            raise RuntimeError("Fetcher must be used as async context manager")
        await asyncio.sleep(self.request_delay)
        logger.debug("[%s] GET %s", self.source_name, url)
        response = await self.client.get(url, **kwargs)
        response.raise_for_status()
        return response

    async def _post(self, url: str, **kwargs) -> httpx.Response:
        """Perform a POST request with rate limiting."""
        if not self.client:
            raise RuntimeError("Fetcher must be used as async context manager")
        await asyncio.sleep(self.request_delay)
        logger.debug("[%s] POST %s", self.source_name, url)
        response = await self.client.post(url, **kwargs)
        response.raise_for_status()
        return response

    async def fetch_all(
        self,
        max_pages: int = 10,
        fetch_details: bool = False,
    ) -> list[TenderInfo]:
        """Fetch all pages and optionally fetch details.

        Args:
            max_pages: Maximum number of list pages to fetch.
            fetch_details: Whether to fetch full details for each tender.

        Returns:
            Complete list of TenderInfo objects.
        """
        all_tenders: list[TenderInfo] = []

        for page in range(1, max_pages + 1):
            try:
                tenders = await self.fetch_list(page)
            except Exception:
                logger.exception(
                    "[%s] Failed to fetch page %d",
                    self.source_name, page,
                )
                break

            if not tenders:
                logger.info("[%s] No more results at page %d", self.source_name, page)
                break

            all_tenders.extend(tenders)
            logger.info(
                "[%s] Page %d: fetched %d items (total: %d)",
                self.source_name, page, len(tenders), len(all_tenders),
            )

        if fetch_details:
            detailed: list[TenderInfo] = []
            for tender in all_tenders:
                try:
                    detail = await self.fetch_detail(tender.external_id)
                    detailed.append(detail)
                except Exception:
                    logger.warning(
                        "[%s] Failed to fetch detail for %s, using list data",
                        self.source_name,
                        tender.external_id,
                    )
                    detailed.append(tender)
            return detailed

        return all_tenders
