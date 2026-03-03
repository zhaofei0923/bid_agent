"""Fetchers - API/RSS based data fetchers for multilateral development banks.

This module provides official API and RSS based fetchers for
ADB and World Bank procurement opportunities.

Data Source Notes:
- ADB: Uses https://www.adb.org/rss/procurement-notices (official RSS).
  FeedBurner URLs were replaced because feeds.feedburner.com (Google) is
  blocked by GFW on mainland China servers.
  The direct ADB RSS provides minimal metadata (title + link only, no deadline
  or category fields), so deadline-based filtering is skipped for ADB items.
- AfDB: Currently unsupported — afdb.org blocks server-side requests at the
  WAF/IP level (HTTP 403), making reliable automated fetching impossible.
"""

from app.fetchers.adb import ADBFetcher
from app.fetchers.base import BaseFetcher
from app.fetchers.worldbank import WorldBankFetcher

__all__ = [
    "ADBFetcher",
    "BaseFetcher",
    "WorldBankFetcher",
    "get_fetcher",
]

# Registry of available fetchers
FETCHERS: dict[str, type[BaseFetcher]] = {
    "wb": WorldBankFetcher,
    "worldbank": WorldBankFetcher,
    "adb": ADBFetcher,
}


def get_fetcher(source: str) -> BaseFetcher:
    """Get a fetcher instance by source name.

    Args:
        source: Source identifier (e.g., 'wb', 'adb', 'afdb').

    Returns:
        BaseFetcher instance for the given source.

    Raises:
        ValueError: If source is not supported.
    """
    source = source.lower()
    fetcher_class = FETCHERS.get(source)
    if not fetcher_class:
        available = ", ".join(FETCHERS.keys())
        raise ValueError(
            f"Unknown source: {source}. Available sources: {available}"
        )
    return fetcher_class()
