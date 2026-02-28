"""Knowledge base API routes — CRUD and semantic search."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.security import get_current_user
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new knowledge base."""
    kb = KnowledgeBase(
        name=data.name,
        description=data.description,
        institution=data.institution,
        user_id=current_user.id,
    )
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    return kb


@router.get("/", response_model=list[KnowledgeBaseResponse])
async def list_knowledge_bases(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List knowledge bases for the current user."""
    result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a knowledge base by ID."""
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id,
        )
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise NotFoundError("KnowledgeBase", str(kb_id))
    return kb


@router.post("/search", response_model=list[KnowledgeSearchResult])
async def search_knowledge(
    request: KnowledgeSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Semantic search across knowledge base."""
    from app.services.knowledge_base_service import KnowledgeBaseService

    service = KnowledgeBaseService(db)
    return await service.search(
        query=request.query,
        institution=request.institution,
        top_k=request.top_k if hasattr(request, "top_k") else 10,
    )
    # TODO: Implement vector search via pgvector
    return []
