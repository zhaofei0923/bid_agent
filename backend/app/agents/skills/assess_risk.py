"""AssessRisk — comprehensive risk assessment and Bid/No-Bid recommendation."""

from app.agents.skills.base import Skill, SkillContext, SkillResult

SYSTEM_PROMPT = (
    "你是专业的多边发展银行投标分析师，擅长风险评估和投标决策。"
    "根据前序分析结果，进行综合风险评估并给出 Bid/No-Bid 建议。"
)

ASSESSMENT_PROMPT = """请根据以下投标分析结果，进行综合风险评估。

=== 前序分析结果 ===
资质分析: {qualification_summary}
评标标准: {criteria_summary}
关键日期: {dates_summary}
提交要求: {submission_summary}
BDS 修改: {bds_summary}
商务条款: {commercial_summary}

=== 参考知识 ===
{kb_context}

请以 JSON 格式返回:
{{
  "risk_dimensions": [
    {{
      "dimension": "qualification|technical|financial|timeline|compliance",
      "risk_level": "low|medium|high|critical",
      "score": 0,
      "factors": [
        {{
          "factor": "风险因素",
          "impact": "high|medium|low",
          "likelihood": "high|medium|low",
          "mitigation": "应对措施"
        }}
      ]
    }}
  ],
  "overall_risk_score": 0,
  "bid_recommendation": {{
    "decision": "bid|conditional_bid|no_bid",
    "confidence": 0.0,
    "rationale": "决策理由",
    "conditions": ["条件 (如 conditional_bid)"],
    "key_strengths": ["优势点"],
    "key_weaknesses": ["劣势点"]
  }},
  "estimated_win_probability": {{
    "low": 0.0,
    "mid": 0.0,
    "high": 0.0,
    "assumptions": ["估算假设"]
  }},
  "action_items": [
    {{
      "priority": "immediate|short_term|ongoing",
      "action": "行动项",
      "responsible": "负责方",
      "deadline": "截止日期或时段"
    }}
  ]
}}
"""


class AssessRisk(Skill):
    """Comprehensive 5-dimension risk assessment with Bid/No-Bid recommendation.

    This skill depends on results from the six preceding analysis steps:
    - AnalyzeQualification
    - EvaluateCriteria
    - ExtractDates
    - ExtractSubmission
    - AnalyzeBDS
    - AnalyzeCommercial
    """

    name = "assess_risk"
    description = "综合 5 维风险评估和 Bid/No-Bid 建议"

    async def execute(self, ctx: SkillContext) -> SkillResult:
        # Gather summaries from prior analysis results
        qualification_summary = ctx.parameters.get(
            "qualification_summary", "未分析"
        )
        criteria_summary = ctx.parameters.get("criteria_summary", "未分析")
        dates_summary = ctx.parameters.get("dates_summary", "未分析")
        submission_summary = ctx.parameters.get(
            "submission_summary", "未分析"
        )
        bds_summary = ctx.parameters.get("bds_summary", "未分析")
        commercial_summary = ctx.parameters.get(
            "commercial_summary", "未分析"
        )
        kb_context = ctx.parameters.get("kb_context", "")

        prompt = ASSESSMENT_PROMPT.format(
            qualification_summary=qualification_summary,
            criteria_summary=criteria_summary,
            dates_summary=dates_summary,
            submission_summary=submission_summary,
            bds_summary=bds_summary,
            commercial_summary=commercial_summary,
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
