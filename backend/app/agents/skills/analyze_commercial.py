"""AnalyzeCommercial — analyze commercial and contractual terms."""

from app.agents.skills.base import Skill, SkillContext, SkillResult

SYSTEM_PROMPT = (
    "你是专业的多边发展银行投标分析师，精通合同条款和商务条件分析。"
    "请分析招标文件中的商务和合同条款。"
)

ANALYSIS_PROMPT = """请分析以下招标文件中的商务和合同条款。

=== 招标文件摘录 ===
{bid_context}

=== 参考知识 ===
{kb_context}

请以 JSON 格式返回:
{{
  "payment_terms": {{
    "payment_schedule": [
      {{
        "milestone": "里程碑",
        "percentage": 0,
        "condition": "支付条件"
      }}
    ],
    "advance_payment": {{
      "available": true,
      "percentage": 0,
      "guarantee_required": true
    }},
    "retention": {{
      "percentage": 0,
      "release_condition": "释放条件"
    }},
    "currency": "USD",
    "payment_method": "银行转账/信用证"
  }},
  "guarantees": [
    {{
      "type": "performance|advance_payment|bid_security",
      "percentage": 0,
      "validity": "有效期",
      "form": "bank_guarantee|standby_lc"
    }}
  ],
  "warranty": {{
    "period_months": 0,
    "scope": "保修范围",
    "conditions": "保修条件"
  }},
  "penalties": {{
    "liquidated_damages": {{
      "rate": "百分比/天或月",
      "cap": "上限",
      "applicable_for": "适用情形"
    }},
    "other_penalties": []
  }},
  "insurance": [
    {{
      "type": "保险类型",
      "minimum_cover": "最低保额",
      "required": true
    }}
  ],
  "dispute_resolution": {{
    "method": "arbitration|litigation|mediation",
    "venue": "仲裁/诉讼地",
    "governing_law": "适用法律",
    "rules": "仲裁规则 (如 ICC/UNCITRAL)"
  }},
  "risk_summary": "商务条款整体风险评估"
}}
"""


class AnalyzeCommercial(Skill):
    """Analyze payment terms, guarantees, penalties, and contractual risks."""

    name = "analyze_commercial"
    description = "分析付款条件、保函、保修、违约金、保险和争议解决等商务条款"

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
