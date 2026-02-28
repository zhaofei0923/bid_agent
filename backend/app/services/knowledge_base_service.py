"""Knowledge base service — CRUD + vector management."""

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.knowledge_base import KnowledgeBase, KnowledgeChunk, KnowledgeDocument

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """Service for managing knowledge bases and their documents."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        name: str,
        institution: str,
        kb_type: str = "procurement_guide",
        description: str = "",
    ) -> KnowledgeBase:
        """Create a new knowledge base."""
        kb = KnowledgeBase(
            name=name,
            institution=institution,
            kb_type=kb_type,
            description=description,
        )
        self.db.add(kb)
        await self.db.commit()
        await self.db.refresh(kb)
        return kb

    async def get_by_id(self, kb_id: UUID) -> KnowledgeBase:
        """Get a knowledge base by ID."""
        result = await self.db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        kb = result.scalar_one_or_none()
        if not kb:
            raise NotFoundError("KnowledgeBase", str(kb_id))
        return kb

    async def list_all(
        self,
        institution: str | None = None,
        kb_type: str | None = None,
    ) -> list[KnowledgeBase]:
        """List knowledge bases with optional filters."""
        query = select(KnowledgeBase)
        if institution:
            query = query.where(KnowledgeBase.institution == institution)
        if kb_type:
            query = query.where(KnowledgeBase.kb_type == kb_type)
        query = query.order_by(KnowledgeBase.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_documents(self, kb_id: UUID) -> list[KnowledgeDocument]:
        """List all documents in a knowledge base."""
        result = await self.db.execute(
            select(KnowledgeDocument)
            .where(KnowledgeDocument.knowledge_base_id == kb_id)
            .order_by(KnowledgeDocument.created_at.desc())
        )
        return list(result.scalars().all())

    async def search(
        self,
        query_embedding: list[float],
        institution: str | None = None,
        kb_type: str | None = None,
        top_k: int = 5,
        score_threshold: float = 0.3,
    ) -> list[dict]:
        """Vector similarity search across knowledge chunks.

        Args:
            query_embedding: 1024-dim embedding vector.
            institution: Filter by institution.
            kb_type: Filter by knowledge base type.
            top_k: Max results.
            score_threshold: Minimum cosine similarity.

        Returns:
            List of matched chunks with metadata and scores.
        """
        try:
            from pgvector.sqlalchemy import Vector
        except ImportError:
            logger.warning("pgvector not available, returning empty results")
            return []

        # Build query with cosine distance
        distance = KnowledgeChunk.embedding.cosine_distance(query_embedding)
        score = (1 - distance).label("score")

        query = (
            select(
                KnowledgeChunk,
                KnowledgeDocument.title.label("document_title"),
                KnowledgeBase.institution,
                score,
            )
            .join(
                KnowledgeDocument,
                KnowledgeChunk.document_id == KnowledgeDocument.id,
            )
            .join(
                KnowledgeBase,
                KnowledgeDocument.knowledge_base_id == KnowledgeBase.id,
            )
            .where(score >= score_threshold)
        )

        if institution:
            query = query.where(KnowledgeBase.institution == institution)
        if kb_type:
            query = query.where(KnowledgeBase.kb_type == kb_type)

        query = query.order_by(distance).limit(top_k)

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "id": str(row.KnowledgeChunk.id),
                "content": row.KnowledgeChunk.content,
                "source_document": row.document_title,
                "institution": row.institution,
                "page_number": row.KnowledgeChunk.page_number,
                "score": float(row.score),
            }
            for row in rows
        ]

    async def delete(self, kb_id: UUID) -> None:
        """Delete a knowledge base and all its documents/chunks."""
        kb = await self.get_by_id(kb_id)
        await self.db.delete(kb)
        await self.db.commit()
        logger.info("Deleted knowledge base %s", kb_id)
