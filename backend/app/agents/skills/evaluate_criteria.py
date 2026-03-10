"""EvaluateCriteria — extract evaluation/scoring criteria from bid documents."""

from app.agents.skills.base import Skill, SkillContext, SkillResult

SYSTEM_PROMPT = (
    "你是专业的多边发展银行投标分析师。"
    "请从招标文件中提取评分标准和方法论，并基于采购指南对评标方法做简要介绍和指导说明。"
)

EXTRACTION_PROMPT = """请从以下招标文件内容中提取完整的评分标准，并介绍该评标方法。

=== 招标文件摘录 ===
{bid_context}

=== 采购指南参考 ===
{kb_context}

请以 JSON 格式返回:
{{
  "evaluation_method": {{
    "type": "QCBS|QBS|FBS|LCS|CQS|ICB|NCB|other",
    "full_name": "完整名称",
    "introduction": "基于采购指南的方法介绍（该方法的适用范围、特点、注意事项，150字以内）",
    "guidance_notes": "对投标人的指导说明（该方法下的中标关键策略，100字以内）"
  }},
  "technical_weight": 80,
  "financial_weight": 20,
  "technical_criteria": [
    {{
      "criterion": "评分大类",
      "weight": 30,
      "sub_criteria": [
        {{"name": "子项", "max_score": 15, "scoring_hint": "评分要点提示"}}
      ]
    }}
  ],
  "financial_evaluation": {{
    "formula": "Sf = 100 * Fm / F",
    "description": "财务评分计算说明"
  }},
  "qualification_thresholds": {{
    "technical_minimum": 75,
    "description": "最低技术分说明"
  }},
  "scoring_tips": [
    "评分策略提示1（如：技术权重高于财务，应重点投入技术方案质量）",
    "评分策略提示2"
  ]
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
