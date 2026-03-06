"""Bid Analysis Pipeline — 8-step incremental analysis.

Runs analysis Skills in order, supports selective steps and caching.
Independent steps (1-7) execute in parallel; risk_assessment runs last.
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm_client import get_llm_client
from app.agents.rag import build_analysis_context
from app.agents.skills.analyze_bds import AnalyzeBDS
from app.agents.skills.analyze_commercial import AnalyzeCommercial
from app.agents.skills.analyze_qualification import AnalyzeQualification
from app.agents.skills.assess_risk import AssessRisk
from app.agents.skills.base import Skill, SkillContext
from app.agents.skills.evaluate_criteria import EvaluateCriteria
from app.agents.skills.evaluate_methodology import EvaluateMethodology
from app.agents.skills.extract_dates import ExtractDates
from app.agents.skills.extract_submission import ExtractSubmission
from app.models.bid_analysis import BidAnalysis
from app.models.project import Project

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

# Maps step names → Skill classes (each dedicated Skill).
STEP_SKILL_MAP: dict[str, type[Skill]] = {
    "qualification": AnalyzeQualification,
    "evaluation": EvaluateCriteria,
    "key_dates": ExtractDates,
    "submission": ExtractSubmission,
    "bds_modification": AnalyzeBDS,
    "methodology": EvaluateMethodology,
    "commercial": AnalyzeCommercial,
    "risk_assessment": AssessRisk,
}

# Map step → RAG dimension (for build_analysis_context)
STEP_DIMENSION_MAP: dict[str, str] = {
    "qualification": "qualification",
    "evaluation": "evaluation",
    "key_dates": "dates",
    "submission": "submission",
    "bds_modification": "bds",
    "methodology": "evaluation",
    "commercial": "commercial",
    "risk_assessment": "qualification",  # uses prior results, not new retrieval
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
        "qualification": "qualification_requirements",
        "evaluation": "evaluation_criteria",
        "key_dates": "key_dates",
        "submission": "submission_checklist",
        "bds_modification": "bds_modifications",
        "methodology": "evaluation_methodology",
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

    Independent steps (1-7) run in parallel to avoid HTTP timeouts.
    risk_assessment runs last because it needs the other steps' results.

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

    # Fetch project institution for knowledge base filtering
    proj_result = await db.execute(select(Project).where(Project.id == project_id))
    project = proj_result.scalar_one_or_none()
    institution = project.institution if project and project.institution else "adb"
    # Map "other" to "adb" as fallback (no dedicated KB)
    kb_institution: str | None = institution if institution in ("adb", "wb") else None

    # Load existing analysis (cache)
    analysis = await _get_cached_analysis(db, project_id)

    # Identify which steps actually need execution
    pending_steps: list[str] = []
    for step in steps:
        field = _step_field_name(step)
        if not force_refresh and analysis is not None:
            cached = getattr(analysis, field, None)
            if cached:
                results[step] = cached
                logger.info("Step '%s' loaded from cache for project %s", step, project_id)
                continue
        pending_steps.append(step)

    # Separate risk_assessment (depends on all others) from independent steps
    independent_steps = [s for s in pending_steps if s != "risk_assessment"]
    run_risk = "risk_assessment" in pending_steps

    # Phase 1: Fetch RAG contexts for independent steps sequentially (shares db session)
    step_contexts: dict[str, tuple[str, str]] = {}
    for step in independent_steps:
        dimension = STEP_DIMENSION_MAP.get(step, step)
        try:
            bid_ctx, kb_ctx = await build_analysis_context(
                project_id=project_id,
                dimension=dimension,
                db=db,
                institution=kb_institution,
            )
        except Exception:
            logger.warning("Context retrieval failed for step '%s'", step, exc_info=True)
            bid_ctx, kb_ctx = "", ""
        step_contexts[step] = (bid_ctx, kb_ctx)

    # Phase 2: Run LLM calls for independent steps in parallel
    # Skills do not access ctx.db, so concurrent execution is safe.
    async def _execute_step(step: str) -> tuple[str, dict | None, int]:
        skill_cls = STEP_SKILL_MAP.get(step)
        if skill_cls is None:
            logger.warning("No Skill mapped for step '%s', skipping", step)
            return step, None, 0

        bid_ctx, kb_ctx = step_contexts.get(step, ("", ""))
        ctx = SkillContext(
            project_id=project_id,
            db=db,
            llm_client=llm_client,
            parameters={"bid_context": bid_ctx, "kb_context": kb_ctx},
        )
        skill = skill_cls()
        logger.info("Running step '%s' for project %s (parallel) …", step, project_id)
        try:
            result = await skill.execute(ctx)
            if result.success:
                return step, result.data, result.tokens_consumed
            logger.error("Step '%s' failed: %s", step, result.error)
            return step, {"error": result.error}, 0
        except Exception:
            logger.exception("Unhandled error in step '%s'", step)
            return step, {"error": "internal_error"}, 0

    if independent_steps:
        parallel_results = await asyncio.gather(
            *[_execute_step(s) for s in independent_steps]
        )
        for step, data, tokens in parallel_results:
            if data is not None:
                results[step] = data
            total_tokens += tokens

    # Phase 3: risk_assessment — runs after all others so it can summarise them
    if run_risk:
        import json as _json

        def _summarise(data: Any, max_chars: int = 500) -> str:
            if not data:
                return "未分析"
            s = _json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else str(data)
            return s[:max_chars]

        dimension = STEP_DIMENSION_MAP.get("risk_assessment", "risk_assessment")
        try:
            bid_ctx, kb_ctx = await build_analysis_context(
                project_id=project_id,
                dimension=dimension,
                db=db,
                institution=kb_institution,
            )
        except Exception:
            logger.warning("Context retrieval failed for step 'risk_assessment'", exc_info=True)
            bid_ctx, kb_ctx = "", ""

        extra_params: dict[str, Any] = {
            "qualification_summary": _summarise(results.get("qualification")),
            "criteria_summary": _summarise(results.get("evaluation")),
            "dates_summary": _summarise(results.get("key_dates")),
            "submission_summary": _summarise(results.get("submission")),
            "bds_summary": _summarise(results.get("bds_modification")),
            "commercial_summary": _summarise(results.get("commercial")),
            "kb_context": kb_ctx,
        }

        ctx = SkillContext(
            project_id=project_id,
            db=db,
            llm_client=llm_client,
            parameters={
                **results,
                "bid_context": bid_ctx,
                "kb_context": kb_ctx,
                **extra_params,
            },
        )
        skill = AssessRisk()
        logger.info("Running step 'risk_assessment' for project %s …", project_id)
        try:
            result = await skill.execute(ctx)
            if result.success:
                results["risk_assessment"] = result.data
                total_tokens += result.tokens_consumed
            else:
                logger.error("Step 'risk_assessment' failed: %s", result.error)
                results["risk_assessment"] = {"error": result.error}
        except Exception:
            logger.exception("Unhandled error in step 'risk_assessment'")
            results["risk_assessment"] = {"error": "internal_error"}

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

    analysis.tokens_consumed = (analysis.tokens_consumed or 0) + total_tokens
    analysis.updated_at = datetime.now(UTC)

    await db.commit()
    logger.info(
        "Saved analysis for project %s (%d tokens consumed)",
        project_id,
        total_tokens,
    )
