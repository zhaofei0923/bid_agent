"""Quality review service — full and quick proposal quality assessment."""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm_client import get_llm_client
from app.agents.skills.quality_review import QualityReview
from app.agents.skills.base import SkillContext

logger = logging.getLogger(__name__)


class QualityReviewService:
    """Service for quality review of user proposals."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def full_review(
        self,
        project_id: UUID,
        proposal_content: str,
    ) -> dict[str, Any]:
        """Run a full 4-dimension quality review.

        Dimensions: completeness, compliance, consistency, competitiveness.
        """
        llm = get_llm_client()
        ctx = SkillContext(
            project_id=str(project_id),
            db=self.db,
            llm_client=llm,
            parameters={"mode": "full", "proposal_content": proposal_content},
        )

        skill = QualityReview()
        result = await skill.execute(ctx)

        return {
            "success": result.success,
            "data": result.data,
            "tokens_consumed": result.tokens_consumed,
        }

    async def quick_review(
        self,
        project_id: UUID,
        proposal_summary: str,
    ) -> dict[str, Any]:
        """Run a quick quality check focusing on critical issues."""
        llm = get_llm_client()
        ctx = SkillContext(
            project_id=str(project_id),
            db=self.db,
            llm_client=llm,
            parameters={"mode": "quick", "proposal_content": proposal_summary},
        )

        skill = QualityReview()
        result = await skill.execute(ctx)

        return {
            "success": result.success,
            "data": result.data,
            "tokens_consumed": result.tokens_consumed,
        }
