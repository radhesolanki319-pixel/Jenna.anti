"""Search Provider Abstractions and Implementations."""

import urllib.parse
from abc import ABC, abstractmethod
from typing import Any

from app.ai.tools.types import WebSearchResult


class SearchProvider(ABC):
    """Abstract contract for search engines."""

    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> list[WebSearchResult]:
        """Perform query and return ordered search results with metadata."""
        pass


class MockSearchProvider(SearchProvider):
    """Deterministic in-memory search provider for hermetic testing and offline operation."""

    def __init__(self, predefined_results: dict[str, list[WebSearchResult]] | None = None):
        self._results = predefined_results or {
            "fastapi asyncpg": [
                WebSearchResult(
                    title="FastAPI with AsyncPG and SQLAlchemy 2.0 Guide",
                    url="https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.asyncpg",
                    snippet="FastAPI integrates with asyncpg through SQLAlchemy AsyncEngine for non-blocking PostgreSQL I/O.",
                    domain="docs.sqlalchemy.org",
                    published_date="2025-01-15",
                    score=0.95,
                ),
                WebSearchResult(
                    title="High Performance Python Web APIs with asyncpg",
                    url="https://magicstack.github.io/asyncpg/current/",
                    snippet="asyncpg is the fastest PostgreSQL client library for Python, built natively for asyncio.",
                    domain="magicstack.github.io",
                    published_date="2024-11-20",
                    score=0.91,
                ),
            ],
            "model context protocol": [
                WebSearchResult(
                    title="Model Context Protocol (MCP) Official Documentation",
                    url="https://modelcontextprotocol.io/introduction",
                    snippet="MCP is an open standard protocol enabling AI assistants to securely connect to external tools and data sources.",
                    domain="modelcontextprotocol.io",
                    published_date="2024-12-01",
                    score=0.98,
                ),
                WebSearchResult(
                    title="Building MCP Clients and Servers in Python",
                    url="https://github.com/modelcontextprotocol/python-sdk",
                    snippet="Official Python SDK providing stdio and SSE transport mechanisms for tool discovery and execution.",
                    domain="github.com",
                    published_date="2025-02-10",
                    score=0.92,
                ),
            ],
        }

    async def search(self, query: str, limit: int = 5) -> list[WebSearchResult]:
        q_lower = query.lower()
        # Direct keyword matching
        for key, res in self._results.items():
            if key in q_lower or any(word in q_lower for word in key.split()):
                return res[:limit]

        # Generic fallback results
        return [
            WebSearchResult(
                title=f"Search results for '{query}'",
                url=f"https://en.wikipedia.org/wiki/{urllib.parse.quote(query.replace(' ', '_'))}",
                snippet=f"Comprehensive overview, history, and reference specifications regarding {query}.",
                domain="en.wikipedia.org",
                published_date="2025-03-01",
                score=0.85,
            ),
            WebSearchResult(
                title=f"{query} Documentation and Reference Guide",
                url=f"https://developer.mozilla.org/en-US/search?q={urllib.parse.quote(query)}",
                snippet=f"Technical architectural specifications and practical usage guidelines for {query}.",
                domain="developer.mozilla.org",
                published_date="2025-02-15",
                score=0.80,
            ),
        ][:limit]
