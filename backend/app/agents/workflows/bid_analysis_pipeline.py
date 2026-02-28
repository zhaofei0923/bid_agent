"""Bid Analysis Pipeline — 8-step incremental analysis.

Runs analysis Skills in order, supports selective steps and caching.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm_client import get_llm_client
from app.agents.skills.analyze_qualification import AnalyzeQualification
from app.agents.skills.base import Skill, SkillContext
from app.agents.skills.evaluate_criteria import EvaluateCriteria
from app.agents.skills.quality_review import QualityReview
from app.models.bid_analysis import BidAnalysis

logger = logging.getLogger(__name__)

ALL_STEPS = [
    "qualification",
    "evaluation",
    "key_dates",
    "submission",
    "bds_modification",
    "methodology",
    "commercial",
    "risk_assessment",
]

# Maps step names → Skill classes.
# Steps without a dedicated Skill use a generic AnalyzeQualification as placeholder.
STEP_SKILL_MAP: dict[str, type[Skill]] = {
    "qualification": AnalyzeQualification,
    "evaluation": EvaluateCriteria,
    # TODO: Implement dedicated skills for these steps
    "key_dates": AnalyzeQualification,
    "submission": AnalyzeQualification,
    "bds_modification": AnalyzeQualification,
    "methodology": EvaluateCriteria,
    "commercial": AnalyzeQualification,
    "risk_assessment": QualityReview,
}


async def _get_cached_analysis(
    db: AsyncSession,
    project_id: str,
) -> BidAnalysis | None:
    """Retrieve a cached BidAnalysis row if it exists."""
    result = await db.execute(
        select(BidAnalysis).where(BidAnalysis.project_id == project_id)
    )
    return result.scalar_one_or_none()


def _step_field_name(step: str) -> str:
    """Map a step name to the BidAnalysis JSONB column."""
    mapping = {
        "qualification": "qualification_analysis",
        "evaluation": "evaluation_criteria",
        "key_dates": "key_dates",
        "submission": "submission_requirements",
        "bds_modification": "bds_modifications",
        "methodology": "methodology_analysis",
        "commercial": "commercial_terms",
        "risk_assessment": "risk_assessment",
    }
    return mapping.get(step, step)


async def run_bid_analysis_pipeline(
    project_id: str,
    db: AsyncSession,
    steps: list[str] | None = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Execute the 8-step analysis pipeline.

    Args:
        project_id: Target project UUID.
        db: Async database session.
        steps: Subset of ALL_STEPS to run; defaults to all.
        force_refresh: Re-run even if cached results exist.

    Returns:
        Dict mapping step name → analysis result dict.
    """
    if steps is None:
        steps = list(ALL_STEPS)

    llm_client = get_llm_client()
    results: dict[str, Any] = {}
    total_tokens = 0

    # Load existing analysis (cache)
    analysis = await _get_cached_analysis(db, project_id)

    for step in steps:
        field = _step_field_name(step)

        # Use cache if available and not forcing refresh
        if not force_refresh and analysis is not None:
            cached = getattr(analysis, field, None)
            if cached:
                results[step] = cached
                logger.info("Step '%s' loaded from cache for project %s", step, project_id)
                continue

        # Instantiate Skill and execute
        skill_cls = STEP_SKILL_MAP.get(step)
        if skill_cls is None:
            logger.warning("No Skill mapped for step '%s', skipping", step)
            continue

        ctx = SkillContext(
            project_id=project_id,
            db=db,
            llm_client=llm_client,
            parameters={**results},  # prior results available to later steps
        )

        skill = skill_cls()
        logger.info("Running step '%s' for project %s …", step, project_id)

        try:
            result = await skill.execute(ctx)
            if result.success:
                results[step] = result.data
                total_tokens += result.tokens_consumed
            else:
                logger.error("Step '%s' failed: %s", step, result.error)
                results[step] = {"error": result.error}
        except Exception:
            logger.exception("Unhandled error in step '%s'", step)
            results[step] = {"error": "internal_error"}

    # Persist results into bid_analyses table
    await _save_analysis(db, project_id, results, total_tokens)

    return results


async def _save_analysis(
    db: AsyncSession,
    project_id: str,
    results: dict[str, Any],
    total_tokens: int,
) -> None:
    """Upsert analysis results into the database."""
    analysis = await _get_cached_analysis(db, project_id)

    if analysis is None:
        analysis = BidAnalysis(project_id=project_id)
        db.add(analysis)

    for step, data in results.items():
        field = _step_field_name(step)
        if hasattr(analysis, field):
            setattr(analysis, field, data)

    analysis.total_tokens_consumed = (analysis.total_tokens_consumed or 0) + total_tokens
    analysis.updated_at = datetime.now(UTC)

    await db.commit()
    logger.info(
        "Saved analysis for project %s (%d tokens consumed)",
        project_id,
        total_tokens,
    )
