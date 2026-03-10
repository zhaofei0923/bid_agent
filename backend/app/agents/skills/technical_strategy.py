"""TechnicalStrategy — proposal framework and scoring strategy based on technical requirements."""

from app.agents.skills.base import Skill, SkillContext, SkillResult

SYSTEM_PROMPT = (
    "你是资深的多边发展银行投标策略顾问，擅长制定技术方案框架和得分策略。"
    "基于技术需求分析和评分标准，为投标团队制定最优技术方案策略。"
)

STRATEGY_PROMPT = """基于以下技术需求分析和评分标准，请制定技术方案策略。

=== 技术需求分析 ===
{technical_summary}

=== 评分标准 ===
{evaluation_summary}

=== 招标文件补充 ===
{bid_context}

请以 JSON 格式返回:
{{
  "proposal_framework": {{
    "recommended_structure": [
      {{
        "section": "章节名称",
        "key_content": "该章节核心内容要求",
        "page_estimate": "建议页数",
        "priority": "high|medium|low"
      }}
    ],
    "overall_approach": "技术方案总体策略思路（200字以内）"
  }},
  "scoring_strategy": [
    {{
      "criterion": "评分项",
      "weight": 0,
      "current_assessment": "基于公司一般情况的初步评估",
      "strategy": "得分策略建议",
      "key_evidence": ["应重点展示的证据"],
      "pitfalls": ["常见失分点"]
    }}
  ],
  "differentiators": [
    {{
      "area": "差异化竞争领域",
      "approach": "差异化方法",
      "expected_impact": "预期对评分的影响"
    }}
  ],
  "innovation_opportunities": [
    {{
      "area": "可展现创新的方面",
      "suggestion": "创新建议",
      "alignment_with_scoring": "与评分标准的关联"
    }}
  ],
  "risk_mitigation_plan": [
    {{
      "risk": "识别的技术风险",
      "mitigation_approach": "缓解方案框架",
      "include_in_proposal": true
    }}
  ],
  "win_themes": [
    "核心中标主题1（贯穿技术方案的关键信息）",
    "核心中标主题2"
  ]
}}
"""


class TechnicalStrategy(Skill):
    """Generate proposal framework and scoring strategy."""

    name = "technical_strategy"
    description = "制定技术方案框架、得分策略和差异化竞争建议"

    async def execute(self, ctx: SkillContext) -> SkillResult:
        bid_context = ctx.parameters.get("bid_context", "")
        technical_summary = ctx.parameters.get("technical_summary", "未分析")
        evaluation_summary = ctx.parameters.get("evaluation_summary", "未分析")

        if not bid_context and technical_summary == "未分析":
            return SkillResult(
                success=False,
                error="No technical requirements or bid context provided",
            )

        prompt = STRATEGY_PROMPT.format(
            technical_summary=technical_summary,
            evaluation_summary=evaluation_summary,
            bid_context=bid_context,
        )

        try:
            result = await ctx.llm_client.extract_json(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=4000,
            )
            return SkillResult(
                success=True,
                data=result.data,
                tokens_consumed=result.tokens_used,
            )
        except Exception as e:
            return SkillResult(success=False, error=str(e))
