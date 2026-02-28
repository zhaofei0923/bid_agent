"""Quality review API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.credits import deduct_credits, require_credits
from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.services.project_service import ProjectService
from app.services.quality_review_service import QualityReviewService

router = APIRouter()


class ReviewRequest(BaseModel):
    """Request body for quality review."""

    proposal_content: str


@router.post("/{project_id}/quality-review/full")
async def full_review(
    project_id: UUID,
    request: ReviewRequest,
    cost_info: dict = Depends(require_credits("quality_review_full")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run a full 4-dimension quality review on the proposal (30 credits)."""
    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    review_svc = QualityReviewService(db)
    result = await review_svc.full_review(project_id, request.proposal_content)

    await deduct_credits(
        current_user, cost_info["action"], cost_info["cost"], db,
        reference_id=str(project_id),
    )
    return result


@router.post("/{project_id}/quality-review/quick")
async def quick_review(
    project_id: UUID,
    request: ReviewRequest,
    cost_info: dict = Depends(require_credits("quality_review_quick")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run a quick quality check focusing on critical issues (10 credits)."""
    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    review_svc = QualityReviewService(db)
    result = await review_svc.quick_review(project_id, request.proposal_content)

    await deduct_credits(
        current_user, cost_info["action"], cost_info["cost"], db,
        reference_id=str(project_id),
    )
    return result
