"""BaseCrawler — abstract base class for all opportunity crawlers.

All crawlers (ADB, WB, UNGM) inherit from this class, implementing
`fetch_list()` and `fetch_detail()`.
"""

import asyncio
import logging
import os
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

    source: str                          # adb / wb / un
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


class BaseCrawler(ABC):
    """Abstract base for all opportunity crawlers."""

    source_name: str = ""
    base_url: str = ""
    request_delay: float = settings.CRAWLER_REQUEST_DELAY

    def __init__(self) -> None:
        self.client: httpx.AsyncClient | None = None
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

    @staticmethod
    def _get_proxy() -> str | None:
        """Read proxy from env: CRAWLER_PROXY or HTTPS_PROXY."""
        return os.environ.get("CRAWLER_PROXY") or os.environ.get(
            "HTTPS_PROXY"
        ) or os.environ.get("https_proxy")

    async def __aenter__(self):
        proxy = self._get_proxy()
        self.client = httpx.AsyncClient(
            timeout=30,
            headers=self._headers,
            follow_redirects=True,
            proxy=proxy,
        )
        if proxy:
            logger.info("[%s] Using proxy: %s", self.source_name, proxy)
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
            raise RuntimeError("Crawler must be used as async context manager")
        await asyncio.sleep(self.request_delay)
        logger.debug("[%s] GET %s", self.source_name, url)
        response = await self.client.get(url, **kwargs)
        response.raise_for_status()
        return response

    async def _post(self, url: str, **kwargs) -> httpx.Response:
        """Perform a POST request with rate limiting."""
        if not self.client:
            raise RuntimeError("Crawler must be used as async context manager")
        await asyncio.sleep(self.request_delay)
        logger.debug("[%s] POST %s", self.source_name, url)
        response = await self.client.post(url, **kwargs)
        response.raise_for_status()
        return response

    async def crawl_all(
        self,
        max_pages: int = 10,
        fetch_details: bool = True,
    ) -> list[TenderInfo]:
        """Crawl list pages and optionally fetch details.

        Args:
            max_pages: Maximum number of list pages to crawl.
            fetch_details: Whether to fetch full details for each tender.

        Returns:
            Complete list of TenderInfo objects.
        """
        all_tenders: list[TenderInfo] = []
        consecutive_failures = 0
        max_retries = 2

        for page in range(1, max_pages + 1):
            tenders = None
            for attempt in range(max_retries + 1):
                try:
                    tenders = await self.fetch_list(page)
                    break
                except Exception:
                    if attempt < max_retries:
                        wait = (attempt + 1) * 10
                        logger.warning(
                            "[%s] Page %d attempt %d failed, retrying in %ds...",
                            self.source_name, page, attempt + 1, wait,
                        )
                        await asyncio.sleep(wait)
                    else:
                        logger.exception(
                            "[%s] Failed to fetch page %d after %d attempts",
                            self.source_name, page, max_retries + 1,
                        )

            if tenders is None:
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    logger.error(
                        "[%s] 3 consecutive page failures, stopping",
                        self.source_name,
                    )
                    break
                continue

            if not tenders:
                logger.info("[%s] No more results at page %d", self.source_name, page)
                break

            consecutive_failures = 0
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


class CurlCffiCrawler(BaseCrawler):
    """BaseCrawler subclass that uses curl_cffi for TLS fingerprint
    impersonation.  This bypasses Cloudflare and similar WAFs without
    needing a full headless browser.

    Subclasses use ``self._get()`` / ``self._post()`` — the same API
    as ``BaseCrawler`` — but the underlying HTTP client is curl_cffi
    with browser-grade TLS fingerprints.
    """

    impersonate: str = settings.CRAWLER_IMPERSONATE

    def __init__(self) -> None:
        super().__init__()
        self._session = None

    async def __aenter__(self):
        from curl_cffi.requests import AsyncSession

        self._session = AsyncSession(
            impersonate=self.impersonate,
            timeout=30,
            headers=self._headers,
        )
        logger.info(
            "[%s] curl_cffi session started (impersonate=%s)",
            self.source_name,
            self.impersonate,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
        logger.info("[%s] curl_cffi session closed", self.source_name)

    async def _get(self, url: str, **kwargs):
        """Perform a GET request via curl_cffi with rate limiting."""
        if not self._session:
            raise RuntimeError("Crawler must be used as async context manager")
        await asyncio.sleep(self.request_delay)
        logger.debug("[%s] GET %s", self.source_name, url)
        response = await self._session.get(url, **kwargs)
        response.raise_for_status()
        return response

    async def _post(self, url: str, **kwargs):
        """Perform a POST request via curl_cffi with rate limiting."""
        if not self._session:
            raise RuntimeError("Crawler must be used as async context manager")
        await asyncio.sleep(self.request_delay)
        logger.debug("[%s] POST %s", self.source_name, url)
        response = await self._session.post(url, **kwargs)
        response.raise_for_status()
        return response


class PlaywrightCrawler(BaseCrawler):
    """BaseCrawler subclass that uses Playwright headless browser.

    Use this for sites protected by Cloudflare or requiring JS rendering.
    Subclasses implement ``fetch_list`` / ``fetch_detail`` using
    ``self._goto()`` instead of ``self._get()`` / ``self._post()``.
    """

    async def __aenter__(self):
        from playwright.async_api import async_playwright

        self._pw = await async_playwright().start()
        # Use full Chromium binary (headless=False) with --headless=new
        # flag.  This avoids chromium_headless_shell which is easily
        # detected and blocked by Cloudflare on datacenter IPs.
        self._browser = await self._pw.chromium.launch(
            headless=False,
            args=[
                "--headless=new",
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        self._context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            viewport={"width": 1920, "height": 1080},
            java_script_enabled=True,
        )
        # Remove the webdriver navigator property
        await self._context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            """
        )
        self._context.set_default_timeout(
            settings.PLAYWRIGHT_TIMEOUT
        )
        logger.info("[%s] Playwright browser started", self.source_name)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, "_context"):
            await self._context.close()
        if hasattr(self, "_browser"):
            await self._browser.close()
        if hasattr(self, "_pw"):
            await self._pw.stop()
        logger.info("[%s] Playwright browser closed", self.source_name)

    async def _new_page(self):
        """Create a new page in the current browser context."""
        return await self._context.new_page()

    async def _goto(self, url: str, wait_until: str = "load"):
        """Navigate to *url* in a new page, respecting request_delay.

        Returns the Playwright ``Page`` object (caller must close it).
        """
        await asyncio.sleep(self.request_delay)
        page = await self._new_page()
        logger.debug("[%s] GOTO %s", self.source_name, url)
        await page.goto(url, wait_until=wait_until)
        return page
