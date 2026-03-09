"""bid_document_search — semantic search within project bid documents."""

import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# ── 中英双语投标术语映射 ────────────────────────────────────────────
# 当用户用中文提问时，将关键术语扩展为英文，提升对英文招标文件的检索效果
TERM_MAP: dict[str, list[str]] = {
    "投标保函": ["bid security", "bid bond", "bid guarantee"],
    "投标保证金": ["bid security", "bid bond"],
    "履约保函": ["performance security", "performance bond", "performance guarantee"],
    "预付款保函": ["advance payment security", "advance payment guarantee"],
    "银行保函": ["bank guarantee", "bank bond"],
    "保函金额": ["bid security amount", "security amount", "guarantee amount"],
    "投标保函金额": ["bid security amount", "amount of bid security", "bid security value"],
    "保函有效期": ["bid security validity", "security validity period"],
    "投标货币": ["bid currency", "currency of bid", "local currency", "foreign currency"],
    "投标报价": ["bid price", "contract price", "total bid price", "schedule of prices"],
    "评分标准": ["evaluation criteria", "evaluation methodology", "scoring criteria"],
    "资质要求": ["qualification criteria", "eligibility criteria", "minimum requirements"],
    "截止日期": ["submission deadline", "closing date", "bid deadline"],
    "关键日期": ["submission deadline", "bid opening", "key dates", "bid validity"],
    "时间节点": ["submission deadline", "bid opening date", "project timeline"],
    "开标时间": ["bid opening", "opening of bids", "opening date"],
    "投标有效期": ["bid validity", "validity period"],
    "技术方案": ["technical proposal", "technical approach", "methodology"],
    "报价": ["financial proposal", "price", "cost"],
    "联合体": ["joint venture", "consortium"],
    "关键人员": ["key personnel", "key experts", "key staff"],
    "合同条款": ["contract terms", "general conditions", "special conditions"],
}


def _extract_keywords(text_input: str) -> list[str]:
    """从用户问题中提取关键词，并扩展中英文同义词。"""
    keywords: list[str] = []
    # 提取所有中文词组（2字以上）和英文单词
    chinese_words = re.findall(r"[\u4e00-\u9fff]{2,}", text_input)
    english_words = re.findall(r"[a-zA-Z]{3,}", text_input)
    keywords.extend(chinese_words)
    keywords.extend(english_words)

    # 映射扩展
    for zh_term, en_terms in TERM_MAP.items():
        if zh_term in text_input:
            keywords.extend(en_terms)

    # 去重，过滤极短词
    seen: set[str] = set()
    result: list[str] = []
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower not in seen and len(kw) >= 2:
            seen.add(kw_lower)
            result.append(kw)
    return result


async def keyword_search_chunks(
    db: AsyncSession,
    project_id: str,
    keywords: list[str],
    top_k: int = 10,
) -> list[dict]:
    """全文关键词检索招标文件 chunks（ILIKE 模糊匹配），用于补充向量检索的盲区。

    对英文招标文件内容做大小写不敏感匹配，特别适合精确术语（金额、条款号、专有名词）。

    Args:
        db: Database session.
        project_id: Restrict to this project's documents.
        keywords: 关键词列表（中文或英文）。
        top_k: 最多返回结果数。

    Returns:
        List of dicts compatible with bid_document_search output.
    """
    if not keywords:
        return []

    # 为每个关键词构造 ILIKE 条件
    conditions = " OR ".join(
        f"ch.content ILIKE :kw_{i}" for i in range(len(keywords))
    )
    params: dict = {
        "project_id": project_id,
        "top_k": top_k,
    }
    for i, kw in enumerate(keywords):
        params[f"kw_{i}"] = f"%{kw}%"

    sql = text(f"""
        SELECT ch.content, ch.page_number,
               0.0 AS similarity,
               ch.section_type,
               COALESCE(s.section_title, '') AS section_title,
               ch.clause_reference,
               d.filename AS filename,
               ch.id::text AS chunk_id
        FROM bid_document_chunks ch
        JOIN bid_documents d ON ch.bid_document_id = d.id
        LEFT JOIN bid_document_sections s ON ch.section_id = s.id
        WHERE d.project_id = :project_id
          AND d.status = 'processed'
          AND ({conditions})
        LIMIT :top_k
    """)

    try:
        result = await db.execute(sql, params)
        rows = result.fetchall()
    except Exception:
        return []

    return [
        {
            "id": row.chunk_id,
            "content": row.content,
            "page_number": row.page_number,
            "score": 0.0,  # 关键词匹配无相似度分数
            "section_type": row.section_type,
            "section_title": row.section_title,
            "clause_reference": row.clause_reference,
            "filename": row.filename,
            "match_type": "keyword",
        }
        for row in rows
    ]


async def bid_document_search(
    db: AsyncSession,
    project_id: str,
    query_embedding: list[float],
    section_types: list[str] | None = None,
    top_k: int = 5,
    score_threshold: float = 0.3,
) -> list[dict]:
    """Search bid document chunks via pgvector cosine similarity.

    Args:
        db: Database session.
        project_id: Restrict to this project's documents.
        query_embedding: Query vector (1024-dim).
        section_types: Optional filter on section type (matches ch.section_type).
        top_k: Number of results.
        score_threshold: Minimum cosine similarity.

    Returns:
        List of dicts with content, score, section_type, section_title,
        page_number, clause_reference, filename.
    """
    params: dict = {
        "embedding": str(query_embedding),
        "project_id": project_id,
        "top_k": top_k,
    }

    # When section_types requested, first try SQL-level filtering
    if section_types:
        # Build SQL with section_type IN (...) filter
        type_placeholders = ", ".join(f":st_{i}" for i in range(len(section_types)))
        for i, st in enumerate(section_types):
            params[f"st_{i}"] = st

        sql_filtered = text(f"""
            SELECT ch.content, ch.page_number,
                   1 - (ch.embedding <=> cast(:embedding as vector)) AS similarity,
                   ch.section_type,
                   COALESCE(s.section_title, '') AS section_title,
                   ch.clause_reference,
                   d.filename AS filename,
                   ch.id::text AS chunk_id
            FROM bid_document_chunks ch
            JOIN bid_documents d ON ch.bid_document_id = d.id
            LEFT JOIN bid_document_sections s ON ch.section_id = s.id
            WHERE d.project_id = :project_id
              AND d.status = 'processed'
              AND ch.embedding IS NOT NULL
              AND ch.section_type IN ({type_placeholders})
            ORDER BY ch.embedding <=> cast(:embedding as vector)
            LIMIT :top_k
        """)

        result = await db.execute(sql_filtered, params)
        rows = result.fetchall()

        # If SQL filter returned enough results, use them
        if len(rows) >= 3:
            return [
                {
                    "id": row.chunk_id,
                    "content": row.content,
                    "page_number": row.page_number,
                    "score": float(row.similarity),
                    "section_type": row.section_type,
                    "section_title": row.section_title,
                    "clause_reference": row.clause_reference,
                    "filename": row.filename,
                }
                for row in rows
                if float(row.similarity) >= score_threshold
            ] or [
                {
                    "id": row.chunk_id,
                    "content": row.content,
                    "page_number": row.page_number,
                    "score": float(row.similarity),
                    "section_type": row.section_type,
                    "section_title": row.section_title,
                    "clause_reference": row.clause_reference,
                    "filename": row.filename,
                }
                for row in rows
            ]

        # Not enough section-typed results (e.g. old docs with "full_document"),
        # fall through to unfiltered search below

    # Unfiltered vector search (general fallback)
    sql = text("""
        SELECT ch.content, ch.page_number,
               1 - (ch.embedding <=> cast(:embedding as vector)) AS similarity,
               ch.section_type,
               COALESCE(s.section_title, '') AS section_title,
               ch.clause_reference,
               d.filename AS filename,
               ch.id::text AS chunk_id
        FROM bid_document_chunks ch
        JOIN bid_documents d ON ch.bid_document_id = d.id
        LEFT JOIN bid_document_sections s ON ch.section_id = s.id
        WHERE d.project_id = :project_id
          AND d.status = 'processed'
          AND ch.embedding IS NOT NULL
        ORDER BY ch.embedding <=> cast(:embedding as vector)
        LIMIT :top_k
    """)

    result = await db.execute(sql, params)
    rows = result.fetchall()

    if not rows:
        return []

    scored_rows = [
        {
            "id": row.chunk_id,
            "content": row.content,
            "page_number": row.page_number,
            "score": float(row.similarity),
            "section_type": row.section_type,
            "section_title": row.section_title,
            "clause_reference": row.clause_reference,
            "filename": row.filename,
        }
        for row in rows
    ]

    above_threshold = [r for r in scored_rows if r["score"] >= score_threshold]
    # If threshold filters out all results, fall back to returning top_k un-filtered
    return above_threshold if above_threshold else scored_rows
