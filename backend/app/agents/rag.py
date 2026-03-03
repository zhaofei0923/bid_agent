"""RAG utilities — context assembly and question answering."""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.embedding_client import get_embedding_client
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

    embedding_client = get_embedding_client()

    # 1. Multi-query search on bid documents
    all_chunks: list[dict] = []
    section_types = config.get("section_types")
    for query in config.get("doc_queries", []):
        try:
            emb_result = await embedding_client.embed_text(query)
            chunks = await bid_document_search(
                db=db,
                project_id=project_id,
                query_embedding=emb_result.embedding,
                section_types=section_types if section_types else None,
                top_k=5,
                score_threshold=0.3,
            )
            all_chunks.extend(chunks)
        except Exception:
            logger.warning("Embedding/search failed for query '%s'", query, exc_info=True)

    unique_chunks = _deduplicate_by_id(all_chunks)
    top_chunks = sorted(unique_chunks, key=lambda c: c.get("score", 0), reverse=True)[:15]

    # 2. Knowledge base search
    kb_chunks: list[dict] = []
    for query in config.get("kb_queries", []):
        try:
            emb_result = await embedding_client.embed_text(query)
            results = await knowledge_search(
                db=db,
                query_embedding=emb_result.embedding,
                institution=institution,
                top_k=3,
            )
            kb_chunks.extend(results)
        except Exception:
            logger.warning("KB search failed for query '%s'", query, exc_info=True)

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
    embedding_client = get_embedding_client()

    # 1. Generate embedding for the question
    try:
        emb_result = await embedding_client.embed_text(question)
        query_embedding = emb_result.embedding
    except Exception:
        logger.error("Failed to embed question", exc_info=True)
        return {
            "answer": "embedding服务暂时不可用，无法检索相关内容。",
            "sources": [],
            "tokens_consumed": 0,
        }

    # 2. Search bid documents
    doc_results = await bid_document_search(
        db=db,
        project_id=project_id,
        query_embedding=query_embedding,
        top_k=top_k,
    )

    # 3. Optionally search knowledge base
    kb_results: list[dict] = []
    if use_knowledge_base:
        try:
            kb_results = await knowledge_search(
                db=db,
                query_embedding=query_embedding,
                top_k=3,
            )
        except Exception:
            logger.warning("KB search failed", exc_info=True)

    # 4. Build context
    all_results = doc_results + kb_results
    context = []
    for i, chunk in enumerate(all_results):
        source_label = f"[来源 {i + 1}]"
        section_info = chunk.get("section_title") or chunk.get("section_type", "")
        page = chunk.get("page_number", "?")
        content = chunk.get("content", "")
        context.append(f"{source_label} {section_info} (第{page}页)\n{content}")

    # 5. Generate answer with LLM
    response = await llm_client.generate_with_context(
        question=question,
        context=context,
        system_prompt=RAG_SYSTEM_PROMPT,
    )

    return {
        "answer": response.content,
        "sources": [
            {
                "id": r.get("id", ""),
                "content": r.get("content", ""),
                "filename": r.get("filename") or r.get("source_document", ""),
                "section_title": r.get("section_title", ""),
                "page_number": r.get("page_number"),
                "score": r.get("score", 0),
            }
            for r in all_results
        ],
        "tokens_consumed": response.usage.get("total_tokens", 0),
    }
