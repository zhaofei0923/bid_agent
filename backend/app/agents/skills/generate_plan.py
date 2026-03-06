"""GeneratePlan — generate a structured bid preparation task list from analysis results."""

import json

from app.agents.prompts.plan_generation import (
    PLAN_GENERATION_PROMPT,
    PLAN_GENERATION_SYSTEM_PROMPT,
)
from app.agents.skills.base import Skill, SkillContext, SkillResult

_INSTITUTION_LABELS = {
    "adb": "亚洲开发银行 (ADB)",
    "wb": "世界银行 (World Bank)",
    "other": "其他国际机构",
}


class GeneratePlan(Skill):
    """Generate an AI-powered bid preparation task list from analysis results."""

    name = "generate_plan"
    description = "根据投标分析结果生成结构化任务清单"

    async def execute(self, ctx: SkillContext) -> SkillResult:
        analysis_summary = ctx.parameters.get("analysis_summary", "")
        deadline = ctx.parameters.get("deadline") or "未知"
        institution = ctx.parameters.get("institution", "adb")

        if not analysis_summary:
            return SkillResult(success=False, error="No analysis summary provided")

        institution_label = _INSTITUTION_LABELS.get(institution, institution)
        prompt = PLAN_GENERATION_PROMPT.format(
            analysis_summary=analysis_summary,
            deadline=deadline,
            institution=institution_label,
        )

        try:
            result = await ctx.llm_client.extract_json(
                prompt=prompt,
                system_prompt=PLAN_GENERATION_SYSTEM_PROMPT,
                temperature=0.5,
                max_tokens=4000,
            )
            tasks = result.data.get("tasks", [])
            plan_summary = result.data.get("plan_summary", "")

            # Validate each task has required fields
            validated: list[dict] = []
            for i, task in enumerate(tasks):
                if not isinstance(task, dict) or not task.get("title"):
                    continue
                validated.append(
                    {
                        "title": str(task.get("title", ""))[:500],
                        "description": str(task.get("description", ""))[:2000],
                        "category": task.get("category", "administrative"),
                        "priority": task.get("priority", "medium"),
                        "due_date": task.get("due_date"),
                        "sort_order": task.get("sort_order", i + 1),
                    }
                )

            return SkillResult(
                success=True,
                data={"tasks": validated, "plan_summary": plan_summary},
                tokens_consumed=result.tokens_used,
            )
        except Exception as e:
            return SkillResult(success=False, error=str(e))


def _build_analysis_summary(analysis: object, max_chars: int = 2000) -> str:
    """Extract key information from BidAnalysis to build a compact summary string."""
    parts: list[str] = []

    def _safe_json(obj: object) -> str:
        if obj is None:
            return ""
        if isinstance(obj, str):
            return obj
        try:
            return json.dumps(obj, ensure_ascii=False)
        except Exception:
            return str(obj)

    # Qualification requirements
    qual = getattr(analysis, "qualification_requirements", None)
    if qual:
        parts.append(f"【资质要求】{_safe_json(qual)}")

    # Key dates
    dates = getattr(analysis, "key_dates", None)
    if dates:
        parts.append(f"【关键日期】{_safe_json(dates)}")

    # Submission checklist
    checklist = getattr(analysis, "submission_checklist", None)
    if checklist:
        parts.append(f"【提交清单】{_safe_json(checklist)}")

    # Risk assessment
    risk = getattr(analysis, "risk_assessment", None)
    if risk:
        parts.append(f"【风险评估】{_safe_json(risk)}")

    # Evaluation criteria (brief)
    criteria = getattr(analysis, "evaluation_criteria", None)
    if criteria:
        parts.append(f"【评审标准】{_safe_json(criteria)}")

    full = "\n\n".join(parts)
    return full[:max_chars]


def _extract_deadline(key_dates: dict | None) -> str | None:
    """Extract submission deadline from key_dates analysis result."""
    if not key_dates:
        return None

    date_list = key_dates.get("key_dates") or []
    for entry in date_list:
        if not isinstance(entry, dict):
            continue
        category = entry.get("category", "")
        if "submission" in category or "deadline" in category:
            return entry.get("date")

    # Fallback: look for any date with "截" or "submission" in event name
    for entry in date_list:
        if not isinstance(entry, dict):
            continue
        event = str(entry.get("event", "")).lower()
        if "截" in event or "submission" in event or "deadline" in event:
            return entry.get("date")

    return None
