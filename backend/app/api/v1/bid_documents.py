"""Bid documents API routes — upload, status, list."""

from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.bid_document import BidDocumentResponse, BidDocumentSectionResponse

router = APIRouter()


@router.post(
    "/{project_id}/bid-documents",
    response_model=BidDocumentResponse,
    status_code=201,
)
async def upload_bid_document(
    project_id: UUID,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a bid document (PDF/DOCX) for a project."""
    from app.services.bid_document_service import BidDocumentService
    from app.services.project_service import ProjectService

    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    doc_svc = BidDocumentService(db)
    content = await file.read()
    return await doc_svc.upload(
        project_id,
        filename=file.filename or "upload",
        content=content,
        content_type=file.content_type or "",
    )


@router.get(
    "/{project_id}/bid-documents",
    response_model=list[BidDocumentResponse],
)
async def list_bid_documents(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List bid documents for a project."""
    from app.services.bid_document_service import BidDocumentService
    from app.services.project_service import ProjectService

    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    doc_svc = BidDocumentService(db)
    return await doc_svc.list_by_project(project_id)


@router.get(
    "/{project_id}/bid-documents/{document_id}/sections",
    response_model=list[BidDocumentSectionResponse],
)
async def list_document_sections(
    project_id: UUID,
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List sections of a bid document."""
    from sqlalchemy import select

    from app.models.bid_document import BidDocumentSection
    from app.services.project_service import ProjectService

    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)  # auth check

    result = await db.execute(
        select(BidDocumentSection)
        .where(BidDocumentSection.bid_document_id == document_id)
        .order_by(BidDocumentSection.start_page)
    )
    return result.scalars().all()
