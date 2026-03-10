"""EvaluateMethodology — deep evaluation method analysis."""

from app.agents.skills.base import Skill, SkillContext, SkillResult

SYSTEM_PROMPT = (
    "你是专业的多边发展银行投标分析师，深入理解各类评标方法论。"
    "请深入分析招标文件的评标方法、评分标准和权重体系。"
)

ANALYSIS_PROMPT = """请深入分析以下招标文件的评标方法论，并给出详细的得分策略。

=== 招标文件摘录 ===
{bid_context}

=== 参考知识 ===
{kb_context}

请以 JSON 格式返回:
{{
  "evaluation_method": {{
    "type": "QCBS|QBS|FBS|LCS|CQS",
    "full_name": "完整名称",
    "technical_weight": 0,
    "financial_weight": 0,
    "minimum_technical_score": 0
  }},
  "scoring_criteria": [
    {{
      "category": "评分大类",
      "weight": 0,
      "sub_criteria": [
        {{
          "name": "子项",
          "weight": 0,
          "max_score": 0,
          "scoring_guidance": "评分指引（评委通常如何打分）"
        }}
      ],
      "strategy_tips": "该大类的得分策略建议",
      "common_mistakes": "常见失分原因"
    }}
  ],
  "critical_thresholds": {{
    "minimum_pass_score": 0,
    "minimum_per_criterion": null,
    "financial_formula": "财务评分公式(如 Sf = 100 * Fm / F)",
    "combined_formula": "综合评分公式"
  }},
  "win_strategy": {{
    "high_impact_areas": ["分值占比高且可提升的领域"],
    "differentiators": ["与竞争对手的差异化要素"],
    "minimum_effort_areas": ["满足及格线即可的领域"],
    "resource_allocation": "资源分配建议（将精力集中在哪些评分项上）",
    "overall_recommendation": "总体中标策略建议（200字以内）"
  }},
  "score_simulation": {{
    "optimistic_scenario": {{
      "technical_score": 0,
      "key_assumptions": ["乐观假设"]
    }},
    "conservative_scenario": {{
      "technical_score": 0,
      "key_assumptions": ["保守假设"]
    }},
    "improvement_priorities": [
      {{
        "area": "可提升领域",
        "current_estimate": "预估得分",
        "potential_gain": "潜在提升分数",
        "effort_required": "high|medium|low"
      }}
    ]
  }}
}}
"""


class EvaluateMethodology(Skill):
    """Deep evaluation of scoring methodology and win strategy."""

    name = "evaluate_methodology"
    description = "深入分析评标方法论、评分权重和中标策略"

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
                data=result.data,
                tokens_consumed=result.tokens_used,
            )
        except Exception as e:
            return SkillResult(success=False, error=str(e))
