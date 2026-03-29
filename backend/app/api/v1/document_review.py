"""Document review API routes — per-checklist-item file upload and AI review."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.credits import deduct_credits, require_credits
from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.services.document_review_service import DocumentReviewService
from app.services.project_service import ProjectService

router = APIRouter()

# Max upload size: 10 MB
_MAX_FILE_SIZE = 10 * 1024 * 1024

# Allowed MIME types for uploaded files
_ALLOWED_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}


@router.post("/{project_id}/document-review/item")
async def review_checklist_item(
    project_id: UUID,
    item_title: str = Form(...),
    item_guidance: str | None = Form(None),
    source_section: str | None = Form(None),
    source_excerpt: str | None = Form(None),
    content_text: str | None = Form(None),
    file: UploadFile | None = File(None),
    cost_info: dict = Depends(require_credits("doc_review_item")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Review a single checklist item's drafted content (5 credits).

    Accepts either pasted text (content_text) or a file upload (PDF/image).
    Returns AI review result with score, gaps, and suggestions.
    """
    # Validate project ownership
    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    # Process uploaded file
    file_bytes: bytes | None = None
    file_content_type: str | None = None

    if file and file.filename:
        content_type = file.content_type or ""
        if content_type not in _ALLOWED_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {content_type}。支持 PDF、JPG、PNG、WEBP",
            )
        raw = await file.read()
        if len(raw) > _MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail="文件过大，最大支持 10MB",
            )
        file_bytes = raw
        file_content_type = content_type

    # Require at least one input
    if not content_text and not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="请提供审查内容：粘贴文本或上传文件",
        )

    review_svc = DocumentReviewService(db)
    result = await review_svc.review_item(
        project_id=project_id,
        item_title=item_title,
        item_guidance=item_guidance,
        source_section=source_section,
        source_excerpt=source_excerpt,
        content_text=content_text,
        file_bytes=file_bytes,
        file_content_type=file_content_type,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "AI 审查失败，请重试"),
        )

    # Deduct credits only on success
    await deduct_credits(
        current_user,
        cost_info["action"],
        cost_info["cost"],
        db,
        reference_id=str(project_id),
    )

    return result
