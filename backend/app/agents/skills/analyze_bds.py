"""AnalyzeBDS — analyze Bid Data Sheet modifications to standard provisions."""

from app.agents.skills.base import Skill, SkillContext, SkillResult

SYSTEM_PROMPT = (
    "你是专业的多边发展银行投标分析师，精通 ADB Standard Bidding Documents。"
    "请逐条分析 BDS (Bid Data Sheet) 对 ITB (Instructions to Bidders) "
    "标准条款的修改，判断每项修改的优先级和对投标人的影响。"
)

ANALYSIS_PROMPT = """请分析以下 BDS (Bid Data Sheet) 的内容，逐条识别对标准条款的修改。

=== BDS 内容 ===
{bid_context}

=== 参考知识 (ADB 标准条款) ===
{kb_context}

请以 JSON 格式返回:
{{
  "bds_modifications": [
    {{
      "itb_clause": "ITB x.x",
      "bds_reference": "BDS x",
      "standard_provision": "标准条款原文摘要",
      "modification": "具体修改内容",
      "priority": "critical|high|medium|low",
      "impact_on_bidder": "对投标人的影响说明",
      "action_required": "投标人需要采取的行动"
    }}
  ],
  "critical_changes_summary": "关键修改概述",
  "compliance_checklist": [
    {{
      "item": "需满足的合规要求",
      "bds_reference": "BDS x",
      "status": "must_comply"
    }}
  ]
}}
"""


class AnalyzeBDS(Skill):
    """Analyze BDS modifications to standard ITB provisions."""

    name = "analyze_bds"
    description = "分析 BDS 对标准条款的修改及其对投标人的影响"

    async def execute(self, ctx: SkillContext) -> SkillResult:
        bid_context = ctx.parameters.get("bid_context", "")
        kb_context = ctx.parameters.get("kb_context", "")

        if not bid_context:
            return SkillResult(
                success=False,
                error="No bid context provided",
            )

        prompt = ANALYSIS_PROMPT.format(
            bid_context=bid_context,
            kb_context=kb_context,
        )

        try:
            result = await ctx.llm_client.extract_json(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.2,
                max_tokens=4000,
            )
            return SkillResult(
                success=True,
                data=result,
                tokens_consumed=0,
            )
        except Exception as e:
            return SkillResult(success=False, error=str(e))
