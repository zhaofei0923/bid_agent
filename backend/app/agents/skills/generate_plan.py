"""GeneratePlan — generate a structured bid preparation task list from analysis results."""

import json

from app.agents.prompts.plan_generation import (
    ADB_PLAN_TEMPLATE,
    PLAN_GENERATION_PROMPT,
    PLAN_GENERATION_SYSTEM_PROMPT,
    VALID_CATEGORIES,
    WB_PLAN_TEMPLATE,
)
from app.agents.skills.base import Skill, SkillContext, SkillResult

_INSTITUTION_LABELS = {
    "adb": "亚洲开发银行 (ADB)",
    "wb": "世界银行 (World Bank)",
    "afdb": "非洲开发银行 (AfDB)",
    "other": "其他国际机构",
}


class GeneratePlan(Skill):
    """Generate an AI-powered bid preparation task list from analysis results."""

    name = "generate_plan"
    description = "根据投标分析结果生成结构化任务清单（8 类分类，时间倒推）"

    async def execute(self, ctx: SkillContext) -> SkillResult:
        deadline = ctx.parameters.get("deadline") or "未知"
        institution = ctx.parameters.get("institution", "adb")

        # Structured analysis dimensions (new)
        key_dates = ctx.parameters.get("key_dates") or "暂无"
        qualification_requirements = ctx.parameters.get("qualification_requirements") or "暂无"
        evaluation_criteria = ctx.parameters.get("evaluation_criteria") or "暂无"
        submission_checklist = ctx.parameters.get("submission_checklist") or "暂无"
        commercial_terms = ctx.parameters.get("commercial_terms") or "暂无"
        risk_assessment = ctx.parameters.get("risk_assessment") or "暂无"

        # Pick institution-specific template
        if institution == "wb":
            inst_template = WB_PLAN_TEMPLATE
        else:
            inst_template = ADB_PLAN_TEMPLATE

        institution_label = _INSTITUTION_LABELS.get(institution, institution)
        prompt = PLAN_GENERATION_PROMPT.format(
            institution=institution_label,
            deadline=deadline,
            key_dates=_safe_json(key_dates),
            qualification_requirements=_safe_json(qualification_requirements),
            evaluation_criteria=_safe_json(evaluation_criteria),
            submission_checklist=_safe_json(submission_checklist),
            commercial_terms=_safe_json(commercial_terms),
            risk_assessment=_safe_json(risk_assessment),
            institution_template=inst_template,
        )

        try:
            result = await ctx.llm_client.extract_json(
                prompt=prompt,
                system_prompt=PLAN_GENERATION_SYSTEM_PROMPT,
                temperature=0.4,
                max_tokens=6000,
            )
            tasks = result.data.get("tasks", [])
            plan_summary = result.data.get("plan_summary", "")

            # Validate each task
            validated: list[dict] = []
            for i, task in enumerate(tasks):
                if not isinstance(task, dict) or not task.get("title"):
                    continue
                category = task.get("category", "documents")
                if category not in VALID_CATEGORIES:
                    category = "documents"
                validated.append(
                    {
                        "title": str(task.get("title", ""))[:500],
                        "description": str(task.get("description", ""))[:2000],
                        "category": category,
                        "priority": task.get("priority", "medium")
                        if task.get("priority") in ("high", "medium", "low")
                        else "medium",
                        "due_date": task.get("due_date"),
                        "sort_order": task.get("sort_order", i + 1),
                        "related_document": str(task.get("related_document", "") or "")[:500] or None,
                        "reference_page": task.get("reference_page"),
                    }
                )

            # Ensure every category has at least one task
            covered = {t["category"] for t in validated}
            for cat in VALID_CATEGORIES:
                if cat not in covered:
                    validated.append(
                        {
                            "title": _DEFAULT_TASKS[cat],
                            "description": "",
                            "category": cat,
                            "priority": "medium",
                            "due_date": None,
                            "sort_order": len(validated) + 1,
                            "related_document": None,
                            "reference_page": None,
                        }
                    )

            return SkillResult(
                success=True,
                data={"tasks": validated, "plan_summary": plan_summary},
                tokens_consumed=result.tokens_used,
            )
        except Exception as e:
            return SkillResult(success=False, error=str(e))


# Fallback tasks when LLM misses a category
_DEFAULT_TASKS: dict[str, str] = {
    "documents": "准备公司资质证书与法人授权书",
    "team": "确认项目团队组成与分工",
    "technical": "撰写技术方案核心章节",
    "experience": "整理类似项目业绩材料",
    "financial": "编制财务报价与费用预算",
    "compliance": "完成合规声明与反腐败声明",
    "submission": "文件装订打印与提交准备",
    "review": "内部交叉审查与管理层签批",
}


def _safe_json(obj: object) -> str:
    """Safely serialize an object to JSON string for prompt injection."""
    if obj is None:
        return "暂无"
    if isinstance(obj, str):
        return obj
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)


def _build_analysis_summary(analysis: object, max_chars: int = 2000) -> str:
    """Extract key information from BidAnalysis to build a compact summary string."""
    parts: list[str] = []

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
