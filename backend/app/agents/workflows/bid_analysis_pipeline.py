"""Bid Analysis Pipeline — 12-step incremental analysis.

Runs analysis Skills in three rounds, supports selective steps and caching.
Round 1: independent base analyses (parallel)
Round 2: analyses that depend on Round 1 partial results (parallel)
Round 3: synthesis analyses that depend on earlier results (parallel/sequential)
"""

import asyncio
import json as _json
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
from app.agents.skills.analyze_technical import AnalyzeTechnical
from app.agents.skills.assess_risk import AssessRisk
from app.agents.skills.base import Skill, SkillContext
from app.agents.skills.compliance_matrix import BuildComplianceMatrix
from app.agents.skills.evaluate_criteria import EvaluateCriteria
from app.agents.skills.evaluate_methodology import EvaluateMethodology
from app.agents.skills.executive_summary import ExecutiveSummary
from app.agents.skills.extract_dates import ExtractDates
from app.agents.skills.extract_submission import ExtractSubmission
from app.agents.skills.technical_strategy import TechnicalStrategy
from app.models.bid_analysis import BidAnalysis
from app.models.project import Project

logger = logging.getLogger(__name__)

ALL_STEPS = [
    # Round 1 — independent base analyses
    "executive_summary",
    "key_dates",
    "qualification",
    "evaluation",
    "submission",
    # Round 2 — depend on Round 1 partial results
    "bds_analysis",
    "technical_requirements",
    "commercial",
    "methodology",
    # Round 3 — synthesis / depends on earlier rounds
    "technical_strategy",
    "compliance_matrix",
    "risk_assessment",
]

ROUND_1_STEPS = ["executive_summary", "key_dates", "qualification", "evaluation", "submission"]
ROUND_2_STEPS = ["bds_analysis", "technical_requirements", "commercial", "methodology"]
ROUND_3_STEPS = ["technical_strategy", "compliance_matrix", "risk_assessment"]

# Maps step names → Skill classes (each dedicated Skill).
STEP_SKILL_MAP: dict[str, type[Skill]] = {
    "executive_summary": ExecutiveSummary,
    "qualification": AnalyzeQualification,
    "evaluation": EvaluateCriteria,
    "key_dates": ExtractDates,
    "submission": ExtractSubmission,
    "bds_analysis": AnalyzeBDS,
    "technical_requirements": AnalyzeTechnical,
    "methodology": EvaluateMethodology,
    "commercial": AnalyzeCommercial,
    "technical_strategy": TechnicalStrategy,
    "compliance_matrix": BuildComplianceMatrix,
    "risk_assessment": AssessRisk,
}

# Map step → RAG dimension (for build_analysis_context)
STEP_DIMENSION_MAP: dict[str, str] = {
    "executive_summary": "executive",
    "qualification": "qualification",
    "evaluation": "evaluation",
    "key_dates": "dates",
    "submission": "submission",
    "bds_analysis": "bds",
    "technical_requirements": "technical",
    "methodology": "evaluation",
    "commercial": "commercial",
    "technical_strategy": "technical",
    "compliance_matrix": "compliance",
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
        "executive_summary": "executive_summary",
        "qualification": "qualification_requirements",
        "evaluation": "evaluation_criteria",
        "key_dates": "key_dates",
        "submission": "submission_checklist",
        "bds_analysis": "bds_modifications",
        "technical_requirements": "technical_requirements",
        "methodology": "evaluation_methodology",
        "commercial": "commercial_terms",
        "technical_strategy": "technical_strategy",
        "compliance_matrix": "compliance_matrix",
        "risk_assessment": "risk_assessment",
    }
    return mapping.get(step, step)


def _is_valid_cached(data: Any) -> bool:
    """Check if cached analysis data contains meaningful results.

    Empty/error results should not be treated as valid cache so the step
    gets re-executed on next run.
    """
    if not data or not isinstance(data, dict):
        return False
    if "error" in data:
        return False
    # Check for list-type results that are empty (e.g. bds_modifications: [])
    list_fields = [
        "bds_modifications", "qualification_requirements", "key_dates",
        "compliance_checklist", "scoring_criteria", "deliverables",
    ]
    for field in list_fields:
        if field in data and isinstance(data[field], list) and len(data[field]) == 0:
            # If the primary list field is empty, check statistics
            stats = data.get("statistics", {})
            if isinstance(stats, dict) and stats.get("total_bds_items") == 0:
                return False
    return True


async def run_bid_analysis_pipeline(
    project_id: str,
    db: AsyncSession,
    steps: list[str] | None = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Execute the 12-step analysis pipeline in 3 rounds.

    Round 1 (parallel): executive_summary, key_dates, qualification, evaluation, submission
    Round 2 (parallel): bds_analysis, technical_requirements, commercial, methodology
    Round 3 (parallel): technical_strategy, compliance_matrix, risk_assessment

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
    pending_steps: set[str] = set()
    for step in steps:
        field = _step_field_name(step)
        if not force_refresh and analysis is not None:
            cached = getattr(analysis, field, None)
            if cached and _is_valid_cached(cached):
                results[step] = cached
                logger.info("Step '%s' loaded from cache for project %s", step, project_id)
                continue
        pending_steps.add(step)

    def _summarise(data: Any, max_chars: int = 500) -> str:
        if not data:
            return "未分析"
        s = _json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else str(data)
        return s[:max_chars]

    async def _fetch_context(step: str) -> tuple[str, str]:
        """Fetch RAG context for a step."""
        dimension = STEP_DIMENSION_MAP.get(step, step)
        try:
            return await build_analysis_context(
                project_id=project_id,
                dimension=dimension,
                db=db,
                institution=kb_institution,
            )
        except Exception:
            logger.warning("Context retrieval failed for step '%s'", step, exc_info=True)
            return "", ""

    async def _execute_step(
        step: str,
        bid_ctx: str,
        kb_ctx: str,
        extra_params: dict[str, Any] | None = None,
    ) -> tuple[str, dict | None, int]:
        """Execute a single analysis step."""
        skill_cls = STEP_SKILL_MAP.get(step)
        if skill_cls is None:
            logger.warning("No Skill mapped for step '%s', skipping", step)
            return step, None, 0

        params: dict[str, Any] = {"bid_context": bid_ctx, "kb_context": kb_ctx}
        if extra_params:
            params.update(extra_params)

        ctx = SkillContext(
            project_id=project_id,
            db=db,
            llm_client=llm_client,
            parameters=params,
        )
        skill = skill_cls()
        logger.info("Running step '%s' for project %s …", step, project_id)
        try:
            result = await asyncio.wait_for(
                skill.execute(ctx),
                timeout=90,
            )
            if result.success:
                return step, result.data, result.tokens_consumed
            logger.error("Step '%s' failed: %s", step, result.error)
            return step, {"error": result.error}, 0
        except TimeoutError:
            logger.error("Step '%s' timed out after 90s for project %s", step, project_id)
            return step, {"error": f"step_{step}_timeout"}, 0
        except Exception:
            logger.exception("Unhandled error in step '%s'", step)
            return step, {"error": "internal_error"}, 0

    async def _run_round(
        round_steps: list[str],
        extra_params_fn: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        """Run a round of steps: fetch RAG contexts in parallel, then execute LLM calls in parallel."""
        nonlocal total_tokens

        active_steps = [s for s in round_steps if s in pending_steps]
        if not active_steps:
            return

        # Fetch RAG contexts in parallel (read-only, safe with shared async session)
        ctx_results = await asyncio.gather(*[_fetch_context(step) for step in active_steps])
        step_contexts: dict[str, tuple[str, str]] = dict(zip(active_steps, ctx_results, strict=False))

        # Execute LLM calls in parallel
        tasks = []
        for step in active_steps:
            bid_ctx, kb_ctx = step_contexts[step]
            extra = extra_params_fn.get(step) if extra_params_fn else None
            tasks.append(_execute_step(step, bid_ctx, kb_ctx, extra))

        parallel_results = await asyncio.gather(*tasks)
        for step, data, tokens in parallel_results:
            if data is not None:
                results[step] = data
            total_tokens += tokens

    # ── Round 1: Independent base analyses ──
    await _run_round(ROUND_1_STEPS)

    # ── Round 2: Depends on Round 1 partial results ──
    await _run_round(ROUND_2_STEPS)

    # ── Round 3: Synthesis analyses ──
    round_3_extra: dict[str, dict[str, Any]] = {}

    # technical_strategy needs technical_requirements + evaluation results
    round_3_extra["technical_strategy"] = {
        "technical_summary": _summarise(results.get("technical_requirements")),
        "evaluation_summary": _summarise(results.get("evaluation")),
    }

    # compliance_matrix needs qualification + submission + bds results
    round_3_extra["compliance_matrix"] = {
        "qualification_summary": _summarise(results.get("qualification")),
        "submission_summary": _summarise(results.get("submission")),
        "bds_summary": _summarise(results.get("bds_analysis")),
        "technical_summary": _summarise(results.get("technical_requirements")),
    }

    # risk_assessment needs all prior results
    round_3_extra["risk_assessment"] = {
        "executive_summary": _summarise(results.get("executive_summary")),
        "qualification_summary": _summarise(results.get("qualification")),
        "criteria_summary": _summarise(results.get("evaluation")),
        "dates_summary": _summarise(results.get("key_dates")),
        "submission_summary": _summarise(results.get("submission")),
        "bds_summary": _summarise(results.get("bds_analysis")),
        "technical_summary": _summarise(results.get("technical_requirements")),
        "commercial_summary": _summarise(results.get("commercial")),
    }

    await _run_round(ROUND_3_STEPS, round_3_extra)

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
