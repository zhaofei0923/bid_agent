"""knowledge_search — semantic search across knowledge base chunks."""


from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def knowledge_search(
    db: AsyncSession,
    query_embedding: list[float],
    institution: str | None = None,
    kb_type: str | None = None,
    top_k: int = 5,
    score_threshold: float = 0.5,
) -> list[dict]:
    """Search knowledge base via pgvector cosine similarity.

    Args:
        db: Database session.
        query_embedding: Query vector (1024-dim).
        institution: Filter by institution (adb/wb/un).
        kb_type: Filter by KB type (guide/review/template).
        top_k: Number of results.
        score_threshold: Minimum cosine similarity.

    Returns:
        List of dicts: [{content, score, source_document, page_number}]
    """
    # Build raw SQL for pgvector similarity search
    params: dict = {
        "embedding": str(query_embedding),
        "top_k": top_k,
        "threshold": score_threshold,
    }

    where_clauses = []
    if institution:
        where_clauses.append("kb.institution = :institution")
        params["institution"] = institution
    if kb_type:
        where_clauses.append("kb.kb_type = :kb_type")
        params["kb_type"] = kb_type

    where_sql = " AND ".join(where_clauses)
    if where_sql:
        where_sql = "WHERE " + where_sql

    sql = text(f"""
        SELECT c.content, c.page_number,
               1 - (c.embedding <=> :embedding::vector) AS similarity,
               d.file_name AS source_document
        FROM knowledge_chunks c
        JOIN knowledge_documents d ON c.document_id = d.id
        JOIN knowledge_bases kb ON d.knowledge_base_id = kb.id
        {where_sql}
        ORDER BY c.embedding <=> :embedding::vector
        LIMIT :top_k
    """)

    result = await db.execute(sql, params)
    rows = result.fetchall()

    return [
        {
            "content": row.content,
            "page_number": row.page_number,
            "score": float(row.similarity),
            "source_document": row.source_document,
        }
        for row in rows
        if float(row.similarity) >= score_threshold
    ]
