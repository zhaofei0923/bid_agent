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
    project = await project_svc.get_by_id(project_id, current_user.id)

    doc_svc = BidDocumentService(db)
    content = await file.read()
    doc = await doc_svc.upload(
        project_id,
        filename=file.filename or "upload",
        content=content,
        content_type=file.content_type or "",
    )

    # Promote project from 'draft' to 'created' on first successful upload
    if project.status == "draft":
        project.status = "created"
        project.progress = 10
        await db.commit()

    # Dispatch async processing task (PDF parse → chunk → vectorize)
    try:
        from app.tasks.document_tasks import process_document
        process_document.delay(str(doc.id))
    except Exception:
        import logging
        logging.getLogger(__name__).warning(
            "Celery not available — document %s will remain in 'pending' status", doc.id
        )

    return doc


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


@router.post(
    "/{project_id}/bid-documents/analyze-combined",
    status_code=202,
)
async def analyze_combined_documents(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger unified AI overview generation across all processed documents of a project."""
    from app.services.project_service import ProjectService

    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    try:
        from app.tasks.document_tasks import generate_combined_document_ai
        generate_combined_document_ai.delay(str(project_id))
    except Exception:
        import logging
        logging.getLogger(__name__).warning(
            "Celery not available — combined AI analysis will not run for project %s", project_id
        )

    return {"message": "Combined AI analysis queued", "project_id": str(project_id)}


@router.delete(
    "/{project_id}/bid-documents/{document_id}",
    status_code=204,
)
async def delete_bid_document(
    project_id: UUID,
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a bid document and its file from disk."""
    from app.services.bid_document_service import BidDocumentService
    from app.services.project_service import ProjectService

    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    doc_svc = BidDocumentService(db)
    await doc_svc.delete(document_id)


@router.post(
    "/{project_id}/bid-documents/{document_id}/analyze",
    status_code=202,
)
async def analyze_bid_document(
    project_id: UUID,
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger (or re-trigger) AI overview + reading tips generation for a document."""
    from app.services.bid_document_service import BidDocumentService
    from app.services.project_service import ProjectService

    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    doc_svc = BidDocumentService(db)
    await doc_svc.get_by_id(document_id)  # validates existence

    try:
        from app.tasks.document_tasks import generate_document_ai
        generate_document_ai.delay(str(document_id))
    except Exception:
        import logging
        logging.getLogger(__name__).warning(
            "Celery not available — AI analysis will not run for document %s", document_id
        )

    return {"message": "AI analysis queued", "document_id": str(document_id)}


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


@router.get("/{project_id}/bid-documents/diagnostics")
async def document_diagnostics(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return vectorization diagnostics for all documents in a project.

    Shows per-document chunk count, section_type distribution, and embedding
    coverage — useful for diagnosing why search results may be biased toward
    certain documents.
    """
    from sqlalchemy import func, select, text

    from app.models.bid_document import BidDocument, BidDocumentChunk
    from app.services.project_service import ProjectService

    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    # Per-document summary
    docs_result = await db.execute(
        select(BidDocument).where(BidDocument.project_id == project_id)
    )
    docs = docs_result.scalars().all()

    diagnostics = []
    for doc in docs:
        # Chunk counts
        total_chunks = await db.execute(
            select(func.count()).where(BidDocumentChunk.bid_document_id == doc.id)
        )
        vectorized_chunks = await db.execute(
            select(func.count()).where(
                BidDocumentChunk.bid_document_id == doc.id,
                BidDocumentChunk.embedding.isnot(None),
            )
        )
        # Section type distribution
        section_dist = await db.execute(
            text(
                "SELECT section_type, COUNT(*) as cnt "
                "FROM bid_document_chunks "
                "WHERE bid_document_id = :doc_id "
                "GROUP BY section_type ORDER BY cnt DESC"
            ),
            {"doc_id": str(doc.id)},
        )

        diagnostics.append({
            "document_id": str(doc.id),
            "filename": doc.original_filename or doc.filename,
            "status": doc.status,
            "page_count": doc.page_count,
            "total_chunks": total_chunks.scalar_one(),
            "vectorized_chunks": vectorized_chunks.scalar_one(),
            "section_type_distribution": {
                row[0] or "null": row[1] for row in section_dist.fetchall()
            },
        })

    return {"project_id": str(project_id), "documents": diagnostics}
