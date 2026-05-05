"""Knowledge base API routes — CRUD and semantic search."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.security import get_current_user, require_admin
from app.database import get_db
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResult,
)

router = APIRouter()


@router.post("/", response_model=KnowledgeBaseResponse, status_code=201)
async def create_knowledge_base(
    data: KnowledgeBaseCreate,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new global knowledge base. Admin only."""
    kb = KnowledgeBase(
        name=data.name,
        description=data.description,
        institution=data.institution,
        kb_type=data.kb_type,
    )
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    return kb


@router.get("/", response_model=list[KnowledgeBaseResponse])
async def list_knowledge_bases(
    institution: str | None = Query(None, pattern="^(adb|wb|afdb)$"),
    kb_type: str | None = Query(None, pattern="^(guide|review|template)$"),
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List global knowledge bases visible to the current user."""
    stmt = select(KnowledgeBase).order_by(KnowledgeBase.institution, KnowledgeBase.name)
    if institution:
        stmt = stmt.where(KnowledgeBase.institution == institution)
    if kb_type:
        stmt = stmt.where(KnowledgeBase.kb_type == kb_type)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: UUID,
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a knowledge base by ID."""
    result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise NotFoundError("KnowledgeBase", str(kb_id))
    return kb


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    kb_id: UUID,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a global knowledge base and its documents. Admin only."""
    result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise NotFoundError("KnowledgeBase", str(kb_id))
    await db.delete(kb)
    await db.commit()


@router.post("/search", response_model=list[KnowledgeSearchResult])
async def search_knowledge(
    request: KnowledgeSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Semantic search across knowledge base (pgvector cosine similarity)."""
    from app.agents.embedding_client import get_embedding_client
    from app.services.knowledge_base_service import KnowledgeBaseService

    # Step 1: embed the query string into a vector
    emb_client = get_embedding_client()
    emb_result = await emb_client.embed_text(request.query)

    # Step 2: vector search via pgvector
    service = KnowledgeBaseService(db)
    return await service.search(
        query_embedding=emb_result.embedding,
        institution=request.institution,
        kb_type=request.kb_type,
        top_k=request.top_k,
        score_threshold=request.score_threshold,
    )


@router.post("/{kb_id}/search", response_model=list[KnowledgeSearchResult])
async def search_knowledge_base(
    kb_id: UUID,
    request: KnowledgeSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Semantic search inside one knowledge base."""
    kb = await get_knowledge_base(kb_id, current_user, db)
    scoped_request = request.model_copy(
        update={"institution": kb.institution, "kb_type": kb.kb_type}
    )
    return await search_knowledge(scoped_request, current_user, db)
