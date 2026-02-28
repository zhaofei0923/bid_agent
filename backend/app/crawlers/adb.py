"""ADB (Asian Development Bank) opportunity crawler.

Uses curl_cffi with Safari TLS fingerprint to bypass Cloudflare WAF and
scrape the Drupal-based tenders listing at www.adb.org/projects/tenders.

Page structure (per item):
    <div class="item">
      <div class="item-meta">Status + Deadline</div>
      <div class="item-title"><a href="/node/XXXXXX">Title</a></div>
      <div class="item-summary">ProjectNum; Country; Sector; Posting date</div>
      <div class="item-details">Notice Type, Approval Number, etc.</div>
    </div>

Pagination: ?page=N (0-based), 20 items/page.
"""

import logging
import re
from datetime import datetime

from app.crawlers.base import CurlCffiCrawler, TenderInfo

logger = logging.getLogger(__name__)

# ADB tenders listing — Active status filter only (all procurement types)
_LIST_URL = "https://www.adb.org/projects/tenders/status/active-1576"


class ADBCrawler(CurlCffiCrawler):
    """Crawler for ADB procurement/consulting opportunities.

    Uses curl_cffi with Safari TLS fingerprint impersonation to
    bypass Cloudflare WAF — no headless browser needed.
    """

    source_name = "adb"
    base_url = "https://www.adb.org"

    async def fetch_list(self, page: int = 1) -> list[TenderInfo]:
        """Fetch one page of ADB tender listings."""
        url = _LIST_URL if page == 1 else f"{_LIST_URL}?page={page - 1}"

        response = await self._get(url)
        html = response.text

        # Verify we didn't get a Cloudflare challenge page
        if "just a moment" in html[:2000].lower():
            raise RuntimeError(
                f"Cloudflare blocked page {page}"
            )

        tenders = _parse_items(html, self.base_url)
        logger.info(
            "[adb] Page %d: parsed %d tenders", page, len(tenders)
        )
        return tenders

    async def fetch_detail(self, tender_id: str) -> TenderInfo:
        """Fetch full details for a single ADB tender.

        *tender_id* is expected to be the node ID like ``1126376``.
        """
        url = (
            f"{self.base_url}/node/{tender_id}"
            if not tender_id.startswith("http")
            else tender_id
        )
        response = await self._get(url)
        return _parse_detail_html(response.text, url, tender_id)

    async def crawl_all(
        self,
        max_pages: int = 10,
        fetch_details: bool = False,
    ) -> list[TenderInfo]:
        """Override: default fetch_details=False (list data is sufficient)."""
        return await super().crawl_all(
            max_pages=max_pages, fetch_details=fetch_details
        )


# ── HTML Parsing ──────────────────────────────────────


def _parse_items(html: str, base_url: str) -> list[TenderInfo]:
    """Extract tender items from ADB tenders listing page.

    Each item is a ``<div class="item">`` block containing:
        - .item-meta  (Status, Deadline)
        - .item-title (link + title)
        - .item-summary (project number; country; sector; posting date)
        - .item-details (notice type, approval number)
    """
    tenders: list[TenderInfo] = []

    # Split HTML into item blocks
    # We look for <div class="item"> ... </div> before next item or end
    item_blocks = re.split(r'<div class="item">', html)
    # First block is everything before the first item — skip it
    item_blocks = item_blocks[1:]

    for block in item_blocks:
        try:
            tender = _parse_single_item(block, base_url)
            if tender:
                tenders.append(tender)
        except Exception:
            logger.debug("[adb] Failed to parse an item block")
            continue

    return tenders


def _parse_single_item(block: str, base_url: str) -> TenderInfo | None:
    """Parse a single item block into TenderInfo."""
    # ── Title + link ──
    title_m = re.search(
        r'class="item-title"[^>]*>.*?<a\s+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        block,
        re.DOTALL | re.IGNORECASE,
    )
    if not title_m:
        return None

    href = title_m.group(1).strip()
    title = _strip_html(title_m.group(2)).strip()
    if not title:
        return None

    # external_id: use the node ID from href (e.g. /node/1126376 → 1126376)
    node_m = re.search(r"/node/(\d+)", href)
    ext_id = node_m.group(1) if node_m else href.rstrip("/").split("/")[-1]

    # Filter out non-tender items (e.g. "Contracts Awarded" header blocks
    # that produce ext_id like "main#project-tenders")
    if not re.match(r"^\d+$", ext_id):
        return None

    url = f"{base_url}{href}" if href.startswith("/") else href

    # ── Skip closed / archived items ──
    status_m = re.search(
        r'<span class="(\w+)">(\w+)</span>',
        block[:500],
    )
    if status_m:
        status_text = status_m.group(2).lower()
        if status_text in ("closed", "archived", "awarded"):
            return None

    # ── Meta: Deadline ──
    status = "open"
    deadline = None

    deadline_m = re.search(
        r"Deadline:</span>\s*<span>([^<]+)</span>",
        block,
        re.IGNORECASE,
    )
    if deadline_m:
        deadline = _parse_date(deadline_m.group(1).strip())

    # ── Summary: project_number; country; sector; posting date ──
    summary_m = re.search(
        r'class="item-summary"[^>]*>(.*?)</div>',
        block,
        re.DOTALL | re.IGNORECASE,
    )

    project_number = ""
    country = ""
    sector = ""
    published_at = None

    if summary_m:
        summary_text = summary_m.group(1)

        # Extract posting date
        posting_m = re.search(
            r"Posting\s+date:\s*([\d]+\s+\w+\s+\d{4})",
            summary_text,
            re.IGNORECASE,
        )
        if posting_m:
            published_at = _parse_date(posting_m.group(1).strip())

        # Clean and split the top part (before "Posting date")
        top_part = re.split(r"Posting\s+date", summary_text, flags=re.IGNORECASE)[0]
        top_text = _strip_html(top_part).strip().rstrip(";").strip()

        # Pattern: "57004-001; Uzbekistan; Transport"
        parts = [p.strip() for p in top_text.split(";") if p.strip()]
        if parts:
            # First part is usually project number (digits-digits pattern)
            if re.match(r"\d{4,6}-\d{3}", parts[0]):
                project_number = parts[0]
                parts = parts[1:]
            if parts:
                country = parts[0]
            if len(parts) > 1:
                sector = parts[1]

    # ── Details: notice type, approval number ──
    procurement_type = ""
    details_m = re.search(
        r'class="item-details"[^>]*>(.*?)</div>',
        block,
        re.DOTALL | re.IGNORECASE,
    )
    if details_m:
        details_text = details_m.group(1)
        notice_m = re.search(
            r"Notice Type:</span>\s*<span>([^<]+)</span>",
            details_text,
            re.IGNORECASE,
        )
        if notice_m:
            procurement_type = notice_m.group(1).strip()

    return TenderInfo(
        source="adb",
        external_id=ext_id,
        url=url,
        title=title,
        project_number=project_number or None,
        country=country,
        sector=sector,
        procurement_type=procurement_type,
        published_at=published_at,
        deadline=deadline,
        status=status,
    )


def _parse_detail_html(
    html: str, url: str, tender_id: str
) -> TenderInfo:
    """Parse a tender detail page."""
    title_m = re.search(
        r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL | re.IGNORECASE
    )
    title = _strip_html(title_m.group(1)) if title_m else tender_id

    # Try multiple selectors for description
    description = ""
    for pattern in (
        r'class="[^"]*field--body[^"]*"[^>]*>(.*?)</div>',
        r'class="[^"]*node-content[^"]*"[^>]*>(.*?)</div>',
        r"<article[^>]*>(.*?)</article>",
    ):
        desc_m = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
        if desc_m:
            description = _strip_html(desc_m.group(1))[:2000]
            break

    return TenderInfo(
        source="adb",
        external_id=tender_id,
        url=url,
        title=title,
        description=description,
        status="open",
    )


# ── Helpers ───────────────────────────────────────────


def _strip_html(html: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def _parse_date(value: str | None) -> datetime | None:
    """Best-effort date parsing for ADB date formats."""
    if not value:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%d %b %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%B %d, %Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
    ):
        try:
            return datetime.strptime(value.strip(), fmt)
        except (ValueError, TypeError):
            continue
    return None


def _parse_float(value) -> float | None:
    """Best-effort float parsing."""
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return None
