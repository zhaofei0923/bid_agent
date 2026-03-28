"""RAG utilities — context assembly and question answering."""

import contextlib
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.embedding_client import get_embedding_client, get_translator
from app.agents.llm_client import get_llm_client
from app.agents.mcp.bid_document_search import (
    bid_document_search,
    keyword_search_chunks,
)
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
        "section_types": ["section_3_qualification", "section_2_bds", "section_1_itb", "full_document", "toc_section"],
        "kb_queries": [
            "ADB qualification criteria",
            "eligibility requirements bidder",
        ],
        "keyword_fallback": ["qualification", "eligibility", "experience", "financial capacity"],
    },
    "evaluation": {
        "doc_queries": [
            "evaluation criteria scoring methodology weight",
            "technical proposal evaluation points",
        ],
        "section_types": ["section_3_qualification", "section_2_bds", "full_document", "toc_section"],
        "kb_queries": [
            "QCBS quality cost based selection",
            "merit point criteria",
        ],
        "keyword_fallback": ["evaluation", "scoring", "criteria", "merit point"],
    },
    "dates": {
        "doc_queries": [
            "submission deadline bid opening date",
            "bid validity period",
        ],
        "section_types": ["section_2_bds", "section_1_itb", "full_document", "toc_section"],
        "kb_queries": ["bid submission deadline requirements"],
        "keyword_fallback": ["deadline", "submission", "opening", "validity", "date"],
    },
    "submission": {
        "doc_queries": [
            "submission requirements format copies",
            "bid security guarantee",
        ],
        "section_types": ["section_2_bds", "section_1_itb", "section_4_forms", "full_document", "toc_section"],
        "kb_queries": ["bid submission format requirements"],
        "keyword_fallback": ["submission", "format", "copies", "bid security"],
    },
    "bds": {
        "doc_queries": [
            "BDS bid data sheet modifications",
            "ITB instruction reference",
        ],
        "section_types": ["section_2_bds", "section_1_itb", "full_document", "toc_section"],
        "kb_queries": ["bid data sheet standard bidding document"],
        "keyword_fallback": ["BDS", "Bid Data Sheet", "ITB", "Instructions to Bidders"],
    },
    "commercial": {
        "doc_queries": [
            "payment terms warranty insurance penalty",
            "performance security",
        ],
        "section_types": ["section_2_bds", "part_3_contract", "full_document", "toc_section"],
        "kb_queries": ["contract terms consulting services"],
        "keyword_fallback": ["payment", "warranty", "insurance", "penalty", "performance security"],
    },
    "executive": {
        "doc_queries": [
            "project name country funding source procurement method",
            "invitation for bids contract overview",
            "scope of work objective background",
        ],
        "section_types": ["section_1_itb", "section_2_bds", "full_document", "toc_section"],
        "kb_queries": [
            "procurement method ICB NCB QCBS overview",
        ],
        "keyword_fallback": ["invitation", "procurement", "project", "funding"],
    },
    "technical": {
        "doc_queries": [
            "technical specifications scope of work terms of reference",
            "deliverables milestones implementation schedule",
            "system requirements equipment standards",
            "key personnel qualifications staffing",
        ],
        "section_types": ["part_2_requirements", "section_3_qualification", "section_2_bds", "full_document", "toc_section"],
        "kb_queries": [
            "technical proposal requirements",
            "terms of reference scope of services",
        ],
        "keyword_fallback": ["technical", "scope of work", "terms of reference", "TOR", "deliverables", "specifications"],
    },
    "compliance": {
        "doc_queries": [
            "mandatory requirements must shall obligation",
            "disqualification rejection grounds",
            "eligibility criteria compliance",
        ],
        "section_types": ["section_1_itb", "section_2_bds", "section_3_qualification", "section_4_forms", "full_document", "toc_section"],
        "kb_queries": [
            "bid compliance mandatory requirements",
        ],
        "keyword_fallback": ["mandatory", "shall", "must", "disqualification", "compliance"],
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
    institution: str | None = "adb",
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
            # Roll back aborted transaction so subsequent queries can proceed
            with contextlib.suppress(Exception):
                await db.rollback()
            logger.warning("Embedding/search failed for query '%s'", query, exc_info=True)

    unique_chunks = _deduplicate_by_id(all_chunks)
    top_chunks = sorted(unique_chunks, key=lambda c: c.get("score", 0), reverse=True)[:15]

    # 1b. Keyword fallback — trigger when:
    #   - No section-typed chunks found, OR
    #   - Results come from only 1 document (single-doc dominance problem)
    keyword_fallback = config.get("keyword_fallback")
    if keyword_fallback:
        target_types = set(config.get("section_types") or [])
        has_relevant = target_types and any(
            c.get("section_type") in target_types for c in top_chunks
        )
        doc_count = len({c.get("filename") for c in top_chunks if c.get("filename")})
        needs_fallback = not has_relevant or (doc_count <= 1 and len(top_chunks) > 0)
        if needs_fallback:
            logger.info(
                "Keyword fallback for '%s': has_relevant=%s, doc_count=%d, chunks=%d",
                dimension, has_relevant, doc_count, len(top_chunks),
            )
            try:
                kw_chunks = await keyword_search_chunks(
                    db=db,
                    project_id=project_id,
                    keywords=keyword_fallback,
                    top_k=15,
                )
                # Merge with existing, dedup
                all_chunks.extend(kw_chunks)
                unique_chunks = _deduplicate_by_id(all_chunks)
                top_chunks = sorted(
                    unique_chunks, key=lambda c: c.get("score", 0), reverse=True
                )[:15]
            except Exception:
                with contextlib.suppress(Exception):
                    await db.rollback()
                logger.warning("Keyword fallback failed for '%s'", dimension, exc_info=True)

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
            # Roll back aborted transaction so subsequent queries can proceed
            with contextlib.suppress(Exception):
                await db.rollback()
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

RAG_SYSTEM_PROMPT = """你是一位专业的招标文件分析助手，负责帮助用户深入理解招标文件内容。
招标文件通常为英文，请注意中英文术语对应关系，准确提取关键信息。

规则：
1. 仅基于提供的上下文内容回答，不编造信息
2. 如参考资料中有相关内容，必须直接引用原文并标注[来源N]
3. 引用金额、日期、条款编号时确保准确，抄录原文数字
4. 如确实找不到答案，明确告知用户，并说明可能在哪个章节查找
5. 使用简洁的中文回答，专业术语保留英文原文并附中文说明"""


def _is_chinese(text: str) -> bool:
    """检测文本是否主要为中文（CJK 字符占比 > 20%）。"""
    cjk_count = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    return cjk_count / max(len(text), 1) > 0.2


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

    # 0. 若问题为中文，先翻译为英文用于向量检索（中英文向量空间不同，翻译可显著提升相关性）
    retrieval_query = question  # fallback: 原问题
    if _is_chinese(question):
        try:
            translator = get_translator()
            retrieval_query = await translator.translate_zh_to_en(question)
            logger.debug("Query translated: %r → %r", question, retrieval_query)
        except Exception:
            logger.warning("Translation failed, using original Chinese query for retrieval", exc_info=True)

    # 1. Generate embedding for the question
    try:
        emb_result = await embedding_client.embed_text(retrieval_query)
        query_embedding = emb_result.embedding
    except Exception:
        logger.error("Failed to embed question", exc_info=True)
        return {
            "answer": "embedding服务暂时不可用，无法检索相关内容。",
            "sources": [],
            "tokens_consumed": 0,
        }

    # 2. Search bid documents — 向量检索 + 关键词全量检索合并
    from app.agents.mcp.bid_document_search import (
        _extract_keywords,
        keyword_search_chunks,
    )

    vector_results = await bid_document_search(
        db=db,
        project_id=project_id,
        query_embedding=query_embedding,
        top_k=top_k,
    )
    # 关键词检索：合并中文原问题 + 英文翻译（去重后提取），扩大召回范围
    kw_combined = question if retrieval_query == question else f"{question} {retrieval_query}"
    kw_results = await keyword_search_chunks(
        db=db,
        project_id=project_id,
        keywords=_extract_keywords(kw_combined),
        top_k=top_k,
    )
    seen_ids: set[str] = {r["id"] for r in vector_results}
    merged_doc: list[dict] = list(vector_results)
    for r in kw_results:
        if r["id"] not in seen_ids:
            seen_ids.add(r["id"])
            merged_doc.append(r)
    doc_results = merged_doc

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
    try:
        response = await llm_client.generate_with_context(
            question=question,
            context=context,
            system_prompt=RAG_SYSTEM_PROMPT,
        )
        answer = response.content
        tokens = response.usage.get("total_tokens", 0)
    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        # Return graceful degraded answer when LLM is unavailable
        ctx_preview = context[0][:200] if context else "（无上下文）"
        answer = (
            f"LLM服务暂时不可用（{type(exc).__name__}）。\n\n"
            f"基于检索到的文件内容，以下片段可供参考：\n{ctx_preview}…"
        )
        tokens = 0

    return {
        "answer": answer,
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
        "tokens_consumed": tokens,
    }
