"""Fetchers - API/RSS based data fetchers for multilateral development banks.

This module provides official API and RSS based fetchers for
ADB and World Bank procurement opportunities.

Note: AfDB (African Development Bank) is currently unsupported.
Their website (afdb.org) blocks server-side requests at the WAF/IP level
(HTTP 403), making reliable automated fetching impossible without a proxy.
"""

from app.fetchers.base import BaseFetcher
from app.fetchers.worldbank import WorldBankFetcher
from app.fetchers.adb import ADBFetcher

__all__ = [
    "BaseFetcher",
    "WorldBankFetcher",
    "ADBFetcher",
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
