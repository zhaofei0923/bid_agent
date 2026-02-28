"""Bid analysis service — wraps the 8-step analysis pipeline."""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.workflows.bid_analysis_pipeline import (
    ALL_STEPS,
    run_bid_analysis_pipeline,
)
from app.core.exceptions import NotFoundError
from app.models.bid_analysis import BidAnalysis

logger = logging.getLogger(__name__)


class BidAnalysisService:
    """Service for managing bid analysis results."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_project(self, project_id: UUID) -> BidAnalysis:
        """Get analysis results for a project."""
        result = await self.db.execute(
            select(BidAnalysis).where(BidAnalysis.project_id == project_id)
        )
        analysis = result.scalar_one_or_none()
        if not analysis:
            raise NotFoundError("BidAnalysis", str(project_id))
        return analysis

    async def run_analysis(
        self,
        project_id: UUID,
        steps: list[str] | None = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """Execute the analysis pipeline.

        Args:
            project_id: Target project.
            steps: Subset of ALL_STEPS to run.
            force_refresh: Re-run even if cached.

        Returns:
            Dict mapping step → result.
        """
        return await run_bid_analysis_pipeline(
            project_id=str(project_id),
            db=self.db,
            steps=steps,
            force_refresh=force_refresh,
        )

    async def get_step_result(
        self,
        project_id: UUID,
        step: str,
    ) -> dict | None:
        """Get a single analysis step result."""
        if step not in ALL_STEPS:
            return None

        analysis = await self.get_by_project(project_id)
        field_map = {
            "qualification": "qualification_analysis",
            "evaluation": "evaluation_criteria",
            "key_dates": "key_dates",
            "submission": "submission_requirements",
            "bds_modification": "bds_modifications",
            "methodology": "methodology_analysis",
            "commercial": "commercial_terms",
            "risk_assessment": "risk_assessment",
        }
        field = field_map.get(step, step)
        return getattr(analysis, field, None)
