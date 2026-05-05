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
from datetime import UTC, datetime, time
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
    "prequalification": "https://www.adb.org/rss/tenders/all/all/1611/all/all/all",
}

# Fallback feed: always accessible but provides title+link only (no status metadata).
# Items from this feed are accepted as-is (assumed active) since the feed
# itself only lists active notices.
_FALLBACK_FEED_URL = "https://www.adb.org/rss/procurement-notices"
_FALLBACK_FEED_NAME = "procurement_notices"

# Current ADB tenders page. The old /rss/tenders/... URLs now return 404 in
# some environments; the reader URL is a parseable Markdown view of the same
# official page and also works when Cloudflare blocks non-browser clients.
_TENDERS_PAGE_URL = "https://www.adb.org/projects/tenders"
_TENDERS_READER_URL = "https://r.jina.ai/http://https://www.adb.org/projects/tenders"
_NODE_READER_URL_TEMPLATE = "https://r.jina.ai/http://https://www.adb.org/node/{node_id}"

# ADB's Projects & Tenders page is backed by a public SearchStax index. This
# endpoint is more complete than the first-page reader fallback and supports
# offset pagination through start/rows.
_SEARCHSTAX_URL = (
    "https://searchcloud-2-ap-southeast-1.searchstax.com/29847/"
    "tenders-11959/emselect"
)
_SEARCHSTAX_AUTH = "2a076eb3a48fd68fc78506c1a16a5d5000da76e4"
_SEARCHSTAX_ROWS = 100
_SEARCHSTAX_FACET_FIELDS = (
    "sm_fct_country",
    "sm_fct_sector",
    "sm_fct_type",
    "ss_fct_group",
    "sm_fct_status",
    "its_fct_year",
)
_SEARCHSTAX_ACTIVE_FILTER = '{!tag=sm_fct_status}sm_fct_status:"Active"'
_SEARCHSTAX_GOODS_FILTER = '{!tag=ss_fct_group}ss_fct_group:"goods"'
_SEARCHSTAX_NOTICE_FILTER = (
    '{!tag=sm_fct_type}sm_fct_type:"Invitation for Bids" '
    'sm_fct_type:"Invitation for prequalification"'
)

# Statuses considered "open" / worth tracking
_ACTIVE_STATUSES = {"active", "open"}
_ACTIVE_NOTICE_TYPES = {
    "Invitation for Bids",
    "Invitation for Prequalification",
    "Invitation for prequalification",
}


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
        self._goods_only = os.getenv("ADB_GOODS_ONLY", "").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

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
        """Fetch current ADB tender listings.

        Prefer the public SearchStax index behind the official Projects &
        Tenders page. It exposes all active tender rows with proper pagination.
        Fall back to parsing the first reader page when SearchStax is not
        available.
        """
        try:
            tenders = await self._fetch_searchstax_tenders(page)
            if tenders or page > 1:
                logger.info(
                    "[adb] Parsed %d tenders from SearchStax page %d",
                    len(tenders),
                    page,
                )
                return _dedupe_tenders(tenders)
            logger.warning("[adb] No SearchStax tenders on first page")
        except Exception:
            logger.warning("[adb] Failed to fetch SearchStax tenders page %d", page)

        if page > 1:
            return []

        tenders = await self._fetch_current_tenders_page()
        unique_tenders = _dedupe_tenders(tenders)
        logger.info("[adb] Total unique tenders: %d", len(unique_tenders))
        return unique_tenders

    async def _fetch_searchstax_tenders(self, page: int) -> list[TenderInfo]:
        rows = int(os.getenv("ADB_SEARCHSTAX_ROWS", str(_SEARCHSTAX_ROWS)))
        start = max(page - 1, 0) * rows
        params: list[tuple[str, str]] = [
            ("q", "*"),
            ("start", str(start)),
            ("fq", _SEARCHSTAX_ACTIVE_FILTER),
            ("fq", _SEARCHSTAX_NOTICE_FILTER),
            ("facet.limit", "-1"),
            ("facet.sort", "index"),
            ("sort", "ds_date_closing desc"),
            ("spellcheck.correct", "false"),
            ("rows", str(rows)),
            ("model", "Default"),
            ("language", "en"),
        ]
        if self._goods_only:
            params.append(("fq", _SEARCHSTAX_GOODS_FILTER))
        for field in _SEARCHSTAX_FACET_FIELDS:
            params.append(
                ("facet.field", f"{{!key=c_{field} ex={field}}}{field}")
            )

        response = await self._get(
            _SEARCHSTAX_URL,
            params=params,
            headers={
                "Accept": "application/json",
                "Authorization": f"Token {os.getenv('ADB_SEARCHSTAX_AUTH', _SEARCHSTAX_AUTH)}",
            },
        )
        data = response.json()
        docs = data.get("response", {}).get("docs", [])
        return [_parse_searchstax_doc(doc) for doc in docs]

    async def fetch_all(
        self,
        max_pages: int = 10,
        fetch_details: bool = False,
    ) -> list[TenderInfo]:
        tenders = await super().fetch_all(max_pages=max_pages, fetch_details=False)
        if not fetch_details:
            if not self._goods_only:
                return tenders
            if all(
                tender.raw_data.get("procurement_group") == "goods"
                for tender in tenders
            ):
                return tenders

        if not (fetch_details or self._goods_only):
            return tenders

        enriched: list[TenderInfo] = []
        for tender in tenders:
            try:
                detail = await self._fetch_detail_for_tender(tender)
            except Exception:
                logger.warning(
                    "[adb] Failed to enrich %s, using list data",
                    tender.external_id,
                )
                detail = tender

            category = detail.raw_data.get("procurement_category")
            procurement_group = detail.raw_data.get("procurement_group")
            if (
                self._goods_only
                and category != "goods"
                and procurement_group != "goods"
            ):
                logger.info(
                    "[adb] Skipping %s: procurement_category=%s",
                    detail.external_id,
                    category or "unknown",
                )
                continue
            enriched.append(detail)

        logger.info("[adb] Enriched tenders: %d", len(enriched))
        return enriched

    async def fetch_detail(self, tender_id: str) -> TenderInfo:
        """Fetch full details for a single ADB tender."""
        return await self._fetch_detail_for_tender(
            TenderInfo(
                source="adb",
                external_id=tender_id,
                url=f"{self.base_url}/node/{tender_id}",
                title=f"ADB Tender {tender_id}",
                status="open",
            )
        )

    async def _fetch_current_tenders_page(self) -> list[TenderInfo]:
        """Fetch and parse the current ADB tenders page."""
        page_url = os.getenv("ADB_TENDERS_URL", _TENDERS_PAGE_URL)
        reader_url = os.getenv("ADB_TENDERS_READER_URL", _TENDERS_READER_URL)

        for url in (page_url, reader_url):
            try:
                response = await self._get(url)
                tenders = _parse_tenders_page(response.text)
                if tenders:
                    logger.info("[adb] Parsed %d tenders from %s", len(tenders), url)
                    return tenders
                logger.warning("[adb] No parseable tenders from %s", url)
            except Exception:
                logger.warning("[adb] Failed to fetch tenders page: %s", url)

        return []

    async def _fetch_detail_for_tender(self, tender: TenderInfo) -> TenderInfo:
        node_url = os.getenv("ADB_NODE_READER_URL_TEMPLATE", _NODE_READER_URL_TEMPLATE)
        url = node_url.format(node_id=tender.external_id)
        response = await self._get(url)
        text = response.text
        category = _classify_adb_detail(text, tender.title)
        deadline = tender.deadline or _parse_adb_deadline_from_detail(text)
        description = _strip_markdown(text)[:2000]

        return TenderInfo(
            source=tender.source,
            external_id=tender.external_id,
            url=tender.url,
            title=tender.title,
            description=description or tender.description,
            organization=tender.organization,
            project_number=tender.project_number,
            published_at=tender.published_at,
            deadline=deadline,
            budget_min=tender.budget_min,
            budget_max=tender.budget_max,
            currency=tender.currency,
            location=tender.location,
            country=tender.country,
            sector=tender.sector,
            procurement_type=(
                "Goods"
                if category == "goods"
                else tender.procurement_type
            ),
            status=tender.status,
            raw_data={**tender.raw_data, "procurement_category": category},
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

        # Skip advance notice items (pre-announcement, not a formal bid)
        if procurement_type in ("Advanced Notice", "Procurement Notice"):
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


def _parse_tenders_page(text: str) -> list[TenderInfo]:
    """Parse ADB Projects & Tenders page text/Markdown."""
    lines = [line.strip() for line in text.splitlines()]
    tenders: list[TenderInfo] = []
    now = datetime.now(UTC)

    for idx, line in enumerate(lines):
        status_match = re.search(
            r"\*\*Status:\*\*(?P<status>[^*]+)\*\*Deadline:\*\*(?P<deadline>.+)",
            line,
        )
        if not status_match:
            continue

        link_line = ""
        link_offset = idx + 1
        for cursor in range(idx + 1, min(idx + 5, len(lines))):
            if lines[cursor]:
                link_line = lines[cursor]
                link_offset = cursor
                break

        link_match = re.match(
            r"^\[(?P<title>.*)\]\((?P<url>https://www\.adb\.org/node/(?P<node_id>\d+))\)",
            link_line,
        )
        if not link_match:
            continue

        metadata_lines: list[str] = []
        for cursor in range(link_offset + 1, min(link_offset + 8, len(lines))):
            if re.search(r"\*\*Status:\*\*", lines[cursor]):
                break
            if lines[cursor]:
                metadata_lines.append(lines[cursor])
            if "**Notice Type:**" in lines[cursor]:
                break
        metadata = "".join(metadata_lines)

        status = status_match.group("status").strip().lower()
        notice_type = _extract_adb_field(metadata, "Notice Type")
        if status not in _ACTIVE_STATUSES or notice_type not in _ACTIVE_NOTICE_TYPES:
            continue

        deadline = _parse_adb_date(status_match.group("deadline"))
        if deadline and deadline < now:
            continue

        title = _clean_adb_title(link_match.group("title"))
        project_number = _extract_project_number(title)

        tenders.append(
            TenderInfo(
                source="adb",
                external_id=link_match.group("node_id"),
                url=link_match.group("url"),
                title=title,
                description=title,
                project_number=project_number,
                published_at=_parse_adb_date(
                    _extract_adb_field(metadata, "Posting Date"),
                    end_of_day=False,
                ),
                deadline=deadline,
                country=_extract_adb_field(metadata, "Country/Economy"),
                sector=_extract_adb_field(metadata, "Sector"),
                procurement_type=notice_type,
                status="open",
                raw_data={"notice_type": notice_type},
            )
        )

    return tenders


def _dedupe_tenders(tenders: list[TenderInfo]) -> list[TenderInfo]:
    seen: set[str] = set()
    unique_tenders: list[TenderInfo] = []
    for tender in tenders:
        if tender.external_id not in seen:
            seen.add(tender.external_id)
            unique_tenders.append(tender)
    return unique_tenders


def _parse_searchstax_doc(doc: dict[str, Any]) -> TenderInfo:
    url_path = _first_doc_value(doc, "ss_url")
    external_id = _extract_node_id(url_path) or _extract_node_id(
        _first_doc_value(doc, "id")
    )
    project_number = _join_doc_values(doc, "tm_X3b_en_project_number")
    title = _build_searchstax_title(
        project_number,
        _join_doc_values(doc, "tm_X3b_en_title"),
    )
    notice_type = _normalise_notice_type(
        _first_doc_value(doc, "tm_X3b_en_type") or "Invitation for Bids"
    )

    return TenderInfo(
        source="adb",
        external_id=external_id,
        url=f"https://www.adb.org{url_path}" if url_path.startswith("/") else url_path,
        title=title,
        description=title,
        project_number=project_number,
        published_at=_parse_searchstax_date(_first_doc_value(doc, "ds_date_posted")),
        deadline=_parse_searchstax_date(_first_doc_value(doc, "ds_date_closing")),
        country=_join_doc_values(doc, "tm_X3b_en_country"),
        sector=_join_doc_values(doc, "tm_X3b_en_sector"),
        procurement_type=f"Goods, Works, and Nonconsulting Services - {notice_type}",
        status="open",
        raw_data={
            "notice_type": notice_type,
            "procurement_group": "goods",
            "source_status": _first_doc_value(doc, "tm_X3b_en_status"),
            "searchstax_id": _first_doc_value(doc, "id"),
        },
    )


def _first_doc_value(doc: dict[str, Any], field: str) -> str:
    value = doc.get(field)
    if isinstance(value, list):
        return str(value[0]).strip() if value else ""
    return str(value).strip() if value is not None else ""


def _join_doc_values(doc: dict[str, Any], field: str) -> str:
    value = doc.get(field)
    if isinstance(value, list):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip() if value is not None else ""


def _extract_node_id(value: str) -> str:
    match = re.search(r"node/(\d+)", value)
    return match.group(1) if match else ""


def _build_searchstax_title(project_number: str, title: str) -> str:
    cleaned = _clean_adb_title(title)
    if project_number and not cleaned.startswith(project_number):
        return f"{project_number}: {cleaned}"
    return cleaned


def _normalise_notice_type(value: str) -> str:
    if value.lower() == "invitation for prequalification":
        return "Invitation for Prequalification"
    return value


def _parse_searchstax_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def _extract_adb_field(text: str, field: str) -> str:
    pattern = rf"\*\*{re.escape(field)}:\*\*(.*?)(?=\*\*[A-Z][^*]+:\*\*|$)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""


def _clean_adb_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.replace("\\", "")).strip(" ]")


def _extract_project_number(title: str) -> str:
    match = re.search(r"\b(\d{5}-\d{3})\b", title)
    return match.group(1) if match else ""


def _parse_adb_date(value: str | None, *, end_of_day: bool = True) -> datetime | None:
    if not value:
        return None
    cleaned = re.sub(r"\s+", " ", value).strip()
    cleaned = re.sub(r"\bat\b.*$", "", cleaned, flags=re.IGNORECASE).strip()

    for fmt in ("%d %b %Y", "%d %B %Y", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(cleaned, fmt)
            parsed_time = time.max if end_of_day else time.min
            return datetime.combine(parsed.date(), parsed_time, tzinfo=UTC)
        except ValueError:
            continue
    return None


def _parse_adb_deadline_from_detail(text: str) -> datetime | None:
    cleaned = re.sub(r"\s+", " ", text)
    match = re.search(
        r"Deadline for Submission of Bids:\s*"
        r"(?P<date>\d{1,2}\s+[A-Za-z]+\s+\d{4})"
        r"(?:\s+at\s+(?P<time>\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?))?",
        cleaned,
    )
    if not match:
        return None

    parsed_date = _parse_adb_date(match.group("date"))
    if not parsed_date:
        return None
    time_text = (match.group("time") or "").strip()
    if time_text:
        for fmt in ("%H:%M", "%I:%M %p"):
            try:
                parsed_time = datetime.strptime(time_text.upper(), fmt).time()
                return datetime.combine(parsed_date.date(), parsed_time, tzinfo=UTC)
            except ValueError:
                continue
    return parsed_date


def _classify_adb_detail(text: str, title: str) -> str:
    lower = f"{title}\n{text}".lower()
    if _is_consulting_type("", lower):
        return "consulting"

    goods_terms = (
        "the purchaser",
        "supply of",
        "supply, delivery",
        "supply and delivery",
        "procurement of",
        "goods",
        "equipment",
        "vehicles",
        "it equipment",
        "medical equipment",
        "materials",
    )
    works_terms = (
        "the works",
        "civil works",
        "construction of",
        "rehabilitation of",
        "road",
        "bridge",
        "building",
        "wastewater",
        "water supply system",
    )

    if any(term in lower for term in works_terms[:5]):
        return "works"

    goods_score = sum(1 for term in goods_terms if term in lower)
    works_score = sum(1 for term in works_terms if term in lower)
    if goods_score > works_score:
        return "goods"
    if works_score:
        return "works"
    if goods_score:
        return "goods"
    return "unknown"


def _strip_markdown(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"URL Source:.*", " ", text)
    text = re.sub(r"Published Time:.*", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[#*_`>]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


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
