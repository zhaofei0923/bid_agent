"""RAG utilities — context assembly and question answering."""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm_client import get_llm_client
from app.agents.mcp.bid_document_search import bid_document_search
from app.agents.mcp.knowledge_search import knowledge_search

logger = logging.getLogger(__name__)

# ── Dimension-specific query configs for analysis context ──

DIMENSION_CONFIGS: dict[str, dict[str, Any]] = {
    "qualification": {
        "doc_queries": [
            "qualification criteria eligibility",
            "minimum experience financial capacity",
            "joint venture consortium",
        ],
        "section_types": ["section_3", "section_2_bds", "section_1_itb"],
        "kb_queries": [
            "ADB qualification criteria",
            "eligibility requirements bidder",
        ],
    },
    "evaluation": {
        "doc_queries": [
            "evaluation criteria scoring methodology weight",
            "technical proposal evaluation points",
        ],
        "section_types": ["section_3", "section_2_bds"],
        "kb_queries": [
            "QCBS quality cost based selection",
            "merit point criteria",
        ],
    },
    "dates": {
        "doc_queries": [
            "submission deadline bid opening date",
            "bid validity period",
        ],
        "section_types": ["section_2_bds", "section_1_itb"],
        "kb_queries": ["bid submission deadline requirements"],
    },
    "submission": {
        "doc_queries": [
            "submission requirements format copies",
            "bid security guarantee",
        ],
        "section_types": ["section_2_bds", "section_1_itb", "section_4_forms"],
        "kb_queries": ["bid submission format requirements"],
    },
    "bds": {
        "doc_queries": [
            "BDS bid data sheet modifications",
            "ITB instruction reference",
        ],
        "section_types": ["section_2_bds", "section_1_itb"],
        "kb_queries": ["bid data sheet standard bidding document"],
    },
    "commercial": {
        "doc_queries": [
            "payment terms warranty insurance penalty",
            "performance security",
        ],
        "section_types": ["section_2_bds", "part_3_contract"],
        "kb_queries": ["contract terms consulting services"],
    },
}


def _deduplicate_by_id(chunks: list[dict]) -> list[dict]:
    """Remove duplicate chunks by their ID, keeping the first occurrence."""
    seen: set[str] = set()
    unique = []
    for chunk in chunks:
        cid = chunk.get("id", "")
        if cid not in seen:
            seen.add(cid)
            unique.append(chunk)
    return unique


async def build_analysis_context(
    project_id: str,
    dimension: str,
    db: AsyncSession,
    institution: str = "adb",
) -> tuple[str, str]:
    """Build analysis context for a specific dimension.

    Returns:
        (bid_document_context, knowledge_context) formatted strings.
    """
    config = DIMENSION_CONFIGS.get(dimension, {})
    if not config:
        return "", ""

    # 1. Multi-query search on bid documents
    all_chunks: list[dict] = []
    for query in config.get("doc_queries", []):
        chunks = await bid_document_search(
            project_id=project_id,
            query=query,
            db=db,
            section_type=config.get("section_types", [None])[0],
            top_k=5,
            score_threshold=0.3,
        )
        all_chunks.extend(chunks)

    unique_chunks = _deduplicate_by_id(all_chunks)
    top_chunks = sorted(unique_chunks, key=lambda c: c.get("score", 0), reverse=True)[:15]

    # 2. Knowledge base search
    kb_chunks: list[dict] = []
    for query in config.get("kb_queries", []):
        results = await knowledge_search(
            query=query,
            db=db,
            institution=institution,
            top_k=3,
        )
        kb_chunks.extend(results)
    top_kb = sorted(kb_chunks, key=lambda c: c.get("score", 0), reverse=True)[:5]

    # 3. Format
    bid_context = "\n\n".join(
        f"[来源 {i + 1}] {c.get('section_title', '')} "
        f"({c.get('clause_reference', '')}) - 第{c.get('page_number', '?')}页\n"
        f"{c.get('content', '')}"
        for i, c in enumerate(top_chunks)
    )

    kb_context = "\n\n".join(
        f"[指南 {i + 1}] {c.get('source_document', '')} - "
        f"第{c.get('page_number', '?')}页\n{c.get('content', '')}"
        for i, c in enumerate(top_kb)
    )

    return bid_context, kb_context


# ── RAG Question Answering ──

RAG_SYSTEM_PROMPT = """你是一位专业的投标文件分析助手。请基于提供的上下文回答用户的问题。

规则：
1. 仅基于提供的上下文内容回答，不编造信息
2. 如果上下文中找不到答案，明确告知用户
3. 引用关键信息时标注来源编号
4. 使用清晰简洁的中文回答
5. 如有数字、日期、金额等，确保准确引用原文"""


async def answer_question(
    project_id: str,
    question: str,
    db: AsyncSession,
    use_knowledge_base: bool = False,
    top_k: int = 5,
) -> dict[str, Any]:
    """RAG question answering over bid documents.

    Args:
        project_id: Project UUID.
        question: User's question in natural language.
        db: Async database session.
        use_knowledge_base: Whether to also search knowledge base.
        top_k: Number of chunks to retrieve.

    Returns:
        Dict with answer text and source chunks.
    """
    llm_client = get_llm_client()

    # 1. Search bid documents
    doc_results = await bid_document_search(
        project_id=project_id,
        query=question,
        db=db,
        top_k=top_k,
    )

    # 2. Optionally search knowledge base
    kb_results: list[dict] = []
    if use_knowledge_base:
        kb_results = await knowledge_search(
            query=question,
            db=db,
            top_k=3,
        )

    # 3. Build context
    context = [chunk.get("content", "") for chunk in doc_results + kb_results]

    # 4. Generate answer with LLM
    response = await llm_client.generate_with_context(
        question=question,
        context=context,
        system_prompt=RAG_SYSTEM_PROMPT,
    )

    return {
        "answer": response.content,
        "sources": doc_results + kb_results,
        "tokens_consumed": response.total_tokens,
    }
