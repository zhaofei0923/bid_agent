"""ExtractDates — extract key dates, timeline, and preparation rhythm from bid documents."""

from app.agents.skills.base import Skill, SkillContext, SkillResult

SYSTEM_PROMPT = (
    "你是专业的多边发展银行投标分析师，精通 ADB、世界银行和 AfDB 采购规程。"
    "请从招标文件中提取所有关键日期和时间节点，并给出准备节奏建议。"
)

EXTRACTION_PROMPT = """请从以下招标文件内容中提取所有关键日期和时间节点，并分析准备节奏。

=== 招标文件摘录 ===
{bid_context}

今天日期: {today}

请以 JSON 格式返回:
{{
  "key_dates": [
    {{
      "event": "事件名称",
      "date": "YYYY-MM-DD 或描述",
      "category": "submission_deadline|clarification_deadline|pre_bid_meeting|site_visit|evaluation_period|contract_start|bid_validity|other",
      "time_zone": "时区 (如 Manila Time)",
      "source_reference": "ITC/ITB x.x",
      "days_from_today": "距今天数（正数=未来，负数=已过，null=无法计算）"
    }}
  ],
  "timeline_summary": {{
    "total_days_from_issue_to_submission": null,
    "clarification_cutoff_before_deadline_days": null,
    "estimated_evaluation_period_days": null,
    "estimated_contract_start": null,
    "remaining_days_to_submission": "距投标截止剩余天数（null=无法计算）"
  }},
  "urgency_assessment": {{
    "level": "red|yellow|green",
    "description": "紧迫程度说明",
    "rationale": "判断依据（如：距截止仅剩X天，而通常准备期需Y天）"
  }},
  "preparation_rhythm": [
    {{
      "milestone": "准备里程碑",
      "suggested_date": "建议完成日期 (YYYY-MM-DD 或相对描述)",
      "days_before_deadline": "距投标截止日的天数",
      "key_tasks": ["该阶段需完成的关键任务"]
    }}
  ],
  "warnings": ["任何时间紧迫或冲突的提醒"]
}}
"""


class ExtractDates(Skill):
    """Extract key dates, timeline, and preparation rhythm from bid documents."""

    name = "extract_dates"
    description = "提取关键日期、倒计时分析和准备节奏建议"

    async def execute(self, ctx: SkillContext) -> SkillResult:
        bid_context = ctx.parameters.get("bid_context", "")

        if not bid_context:
            return SkillResult(
                success=False,
                error="No bid context provided",
            )

        from datetime import UTC, datetime

        today = datetime.now(UTC).strftime("%Y-%m-%d")
        prompt = EXTRACTION_PROMPT.format(bid_context=bid_context, today=today)

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
