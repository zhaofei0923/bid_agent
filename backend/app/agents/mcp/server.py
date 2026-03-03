"""MCP tool registry — in-process tool dispatch for Agent layer.

Provides a ``ToolRegistry`` that maps tool names to their async callables,
enabling the LangGraph workflow nodes to invoke MCP tools by name.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

from app.agents.mcp.bid_document_search import bid_document_search
from app.agents.mcp.knowledge_search import knowledge_search
from app.agents.mcp.opportunity_query import opportunity_query

logger = logging.getLogger(__name__)


@dataclass
class ToolSpec:
    """Metadata for a registered tool."""

    name: str
    description: str
    parameters: dict[str, Any]
    fn: Callable[..., Coroutine[Any, Any, Any]]


@dataclass
class ToolRegistry:
    """Registry that holds all MCP tools and dispatches calls.

    Usage::

        registry = ToolRegistry()
        result = await registry.call("bid_document_search", db=db, project_id="...", ...)
    """

    _tools: dict[str, ToolSpec] = field(default_factory=dict)

    def register(
        self,
        name: str,
        fn: Callable[..., Coroutine[Any, Any, Any]],
        *,
        description: str = "",
        parameters: dict[str, Any] | None = None,
    ) -> None:
        """Register a tool."""
        self._tools[name] = ToolSpec(
            name=name,
            description=description,
            parameters=parameters or {},
            fn=fn,
        )
        logger.debug("Registered MCP tool: %s", name)

    async def call(self, name: str, **kwargs: Any) -> Any:
        """Dispatch a tool call by name.

        Raises:
            KeyError: If tool is not registered.
        """
        if name not in self._tools:
            raise KeyError(f"Unknown MCP tool: {name}")
        logger.info("Calling MCP tool %s", name)
        return await self._tools[name].fn(**kwargs)

    def list_tools(self) -> list[dict[str, Any]]:
        """Return tool metadata for LLM function-calling schema."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            }
            for t in self._tools.values()
        ]

    def __contains__(self, name: str) -> bool:
        return name in self._tools


# ── Singleton ──────────────────────────────────────────────

_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """Return the singleton tool registry with all MCP tools registered."""
    global _registry
    if _registry is not None:
        return _registry

    _registry = ToolRegistry()

    # 1. bid_document_search
    _registry.register(
        "bid_document_search",
        bid_document_search,
        description=(
            "Semantic search within a project's bid document chunks using "
            "pgvector cosine similarity. Returns content, page number, "
            "section info, and similarity score."
        ),
        parameters={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "UUID of the project whose documents to search.",
                },
                "query_embedding": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "1024-dim query vector.",
                },
                "section_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional filter on section_type enum values.",
                },
                "top_k": {"type": "integer", "default": 5},
                "score_threshold": {"type": "number", "default": 0.3},
            },
            "required": ["project_id", "query_embedding"],
        },
    )

    # 2. knowledge_search
    _registry.register(
        "knowledge_search",
        knowledge_search,
        description=(
            "Semantic search across all knowledge base entries (procurement "
            "guides, templates, evaluation references) using pgvector cosine "
            "similarity."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query_embedding": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "1024-dim query vector.",
                },
                "institution": {
                    "type": "string",
                    "enum": ["adb", "wb", "afdb"],
                    "description": "Filter to institution-specific knowledge.",
                },
                "kb_type": {
                    "type": "string",
                    "description": "Filter by KB type.",
                },
                "top_k": {"type": "integer", "default": 5},
                "score_threshold": {"type": "number", "default": 0.5},
            },
            "required": ["query_embedding"],
        },
    )

    # 3. opportunity_query
    _registry.register(
        "opportunity_query",
        opportunity_query,
        description=(
            "Search and filter bidding opportunities from ADB, WB, and AfDB. "
            "Supports keyword search, source/sector/country/status filters."
        ),
        parameters={
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Search keyword."},
                "source": {
                    "type": "string",
                    "enum": ["adb", "wb", "afdb"],
                },
                "sector": {"type": "string"},
                "country": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["open", "closed", "cancelled"],
                },
                "limit": {"type": "integer", "default": 20},
                "offset": {"type": "integer", "default": 0},
            },
            "required": [],
        },
    )

    return _registry
