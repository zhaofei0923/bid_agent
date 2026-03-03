"""bid_document_search — semantic search within project bid documents."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


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
        "threshold": score_threshold,
    }

    section_filter = ""
    if section_types:
        section_filter = "AND ch.section_type = ANY(:section_types)"
        params["section_types"] = section_types

    sql = text(f"""
        SELECT ch.content, ch.page_number,
               1 - (ch.embedding <=> :embedding::vector) AS similarity,
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
          {section_filter}
        ORDER BY ch.embedding <=> :embedding::vector
        LIMIT :top_k
    """)

    result = await db.execute(sql, params)
    rows = result.fetchall()

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
    ]
