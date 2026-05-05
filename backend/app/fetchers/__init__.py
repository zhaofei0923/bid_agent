"""Fetchers - API/RSS based data fetchers for multilateral development banks.

This module provides official API and RSS based fetchers for
ADB, World Bank, and AfDB procurement opportunities.

Data Source Notes:
- ADB: Uses direct ADB RSS URLs (discovered from FeedBurner <source> tags).
  FeedBurner URLs (feeds.feedburner.com) are blocked by GFW on mainland China
  servers. The direct ADB URLs include full category metadata with Status field,
  allowing proper filtering to only Active tenders.
- AfDB: Uses the public AfDB procurement RSS feed. The fetcher fails closed
  and returns an empty list if the upstream WAF blocks the request.
"""

from app.fetchers.adb import ADBFetcher
from app.fetchers.afdb import AfDBFetcher
from app.fetchers.base import BaseFetcher
from app.fetchers.worldbank import WorldBankFetcher

__all__ = [
    "ADBFetcher",
    "AfDBFetcher",
    "BaseFetcher",
    "WorldBankFetcher",
    "get_fetcher",
]

# Registry of available fetchers
FETCHERS: dict[str, type[BaseFetcher]] = {
    "wb": WorldBankFetcher,
    "worldbank": WorldBankFetcher,
    "adb": ADBFetcher,
    "afdb": AfDBFetcher,
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
