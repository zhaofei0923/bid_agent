"""ExtractDates — extract key dates and timeline from bid documents."""

from app.agents.skills.base import Skill, SkillContext, SkillResult

SYSTEM_PROMPT = (
    "你是专业的多边发展银行投标分析师，精通 ADB、世界银行和 AfDB 采购规程。"
    "请从招标文件中提取所有关键日期和时间节点。"
)

EXTRACTION_PROMPT = """请从以下招标文件内容中提取所有关键日期和时间节点。

=== 招标文件摘录 ===
{bid_context}

请以 JSON 格式返回:
{{
  "key_dates": [
    {{
      "event": "事件名称",
      "date": "YYYY-MM-DD 或描述",
      "category": "submission_deadline|clarification_deadline|pre_bid_meeting|site_visit|evaluation_period|contract_start",
      "time_zone": "时区 (如 Manila Time)",
      "source_reference": "ITC/ITB x.x"
    }}
  ],
  "timeline_summary": {{
    "total_days_from_issue_to_submission": null,
    "clarification_cutoff_before_deadline_days": null,
    "estimated_evaluation_period_days": null,
    "estimated_contract_start": null
  }},
  "warnings": ["任何时间紧迫或冲突的提醒"]
}}
"""


class ExtractDates(Skill):
    """Extract key dates and timeline from bid documents."""

    name = "extract_dates"
    description = "提取招标文件中的关键日期和时间节点"

    async def execute(self, ctx: SkillContext) -> SkillResult:
        bid_context = ctx.parameters.get("bid_context", "")

        if not bid_context:
            return SkillResult(
                success=False,
                error="No bid context provided",
            )

        prompt = EXTRACTION_PROMPT.format(bid_context=bid_context)

        try:
            result = await ctx.llm_client.extract_json(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.2,
                max_tokens=2000,
            )
            return SkillResult(
                success=True,
                data=result.data,
                tokens_consumed=result.tokens_used,
            )
        except Exception as e:
            return SkillResult(success=False, error=str(e))
