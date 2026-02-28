"""Bid analysis API routes — trigger analysis, get results."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.workflows.bid_analysis_pipeline import (
    ALL_STEPS,
    run_bid_analysis_pipeline,
)
from app.core.credits import deduct_credits, require_credits
from app.core.exceptions import NotFoundError
from app.core.security import get_current_user
from app.database import get_db
from app.models.bid_analysis import BidAnalysis
from app.models.user import User
from app.services.project_service import ProjectService

router = APIRouter()


@router.get("/{project_id}/analysis")
async def get_analysis(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get bid analysis for a project."""
    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)  # auth check

    result = await db.execute(
        select(BidAnalysis).where(BidAnalysis.project_id == project_id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise NotFoundError("BidAnalysis", str(project_id))
    return analysis


@router.post("/{project_id}/analysis/trigger")
async def trigger_analysis(
    project_id: UUID,
    steps: list[str] | None = Query(None, description="Steps to run"),
    force_refresh: bool = Query(False, description="Re-run even if cached"),
    cost_info: dict = Depends(require_credits("bid_analysis_trigger")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Trigger the 8-step bid analysis pipeline.

    Runs synchronously in-process. For long documents consider
    dispatching to Celery instead.
    """
    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    # Validate step names
    if steps:
        invalid = set(steps) - set(ALL_STEPS)
        if invalid:
            return {"error": f"Unknown steps: {invalid}", "valid_steps": ALL_STEPS}

    results = await run_bid_analysis_pipeline(
        project_id=str(project_id),
        db=db,
        steps=steps,
        force_refresh=force_refresh,
    )

    # Deduct credits after successful run
    new_balance = await deduct_credits(
        current_user,
        cost_info["action"],
        cost_info["cost"],
        db,
        reference_id=str(project_id),
    )

    return {
        "project_id": str(project_id),
        "steps_completed": list(results.keys()),
        "results": results,
        "credits_consumed": cost_info["cost"],
        "credits_remaining": new_balance,
    }
