"""EvaluateCriteria — extract evaluation/scoring criteria from bid documents."""

from app.agents.skills.base import Skill, SkillContext, SkillResult

SYSTEM_PROMPT = (
    "你是专业的多边发展银行投标分析师。"
    "请从招标文件中提取评分标准和方法论，并以 JSON 格式返回。"
)

EXTRACTION_PROMPT = """请从以下招标文件内容中提取完整的评分标准。

=== 招标文件摘录 ===
{bid_context}

=== 参考知识 ===
{kb_context}

请以 JSON 格式返回:
{{
  "evaluation_method": "QCBS|QBS|FBS|LCS|CQS",
  "technical_weight": 80,
  "financial_weight": 20,
  "technical_criteria": [
    {{
      "criterion": "公司经验",
      "weight": 30,
      "sub_criteria": [
        {{"name": "类似项目经验", "max_score": 15}},
        {{"name": "行业专长", "max_score": 15}}
      ]
    }}
  ],
  "financial_evaluation": {{
    "formula": "Sf = 100 * Fm / F",
    "description": "..."
  }},
  "qualification_thresholds": {{
    "technical_minimum": 75
  }}
}}
"""


class EvaluateCriteria(Skill):
    """Extract evaluation criteria from bid documents."""

    name = "evaluate_criteria"
    description = "提取评分标准和方法论"

    async def execute(self, ctx: SkillContext) -> SkillResult:
        bid_context = ctx.parameters.get("bid_context", "")
        kb_context = ctx.parameters.get("kb_context", "")

        if not bid_context:
            return SkillResult(success=False, error="No bid context")

        try:
            result = await ctx.llm_client.extract_json(
                prompt=EXTRACTION_PROMPT.format(
                    bid_context=bid_context, kb_context=kb_context
                ),
                system_prompt=SYSTEM_PROMPT,
                temperature=0.2,
                max_tokens=4000,
            )
            return SkillResult(success=True, data=result.data, tokens_consumed=result.tokens_used)
        except Exception as exc:
            return SkillResult(success=False, error=str(exc))
