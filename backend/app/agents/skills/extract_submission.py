"""ExtractSubmission — extract submission format and requirements."""

from app.agents.skills.base import Skill, SkillContext, SkillResult

SYSTEM_PROMPT = (
    "你是专业的多边发展银行投标分析师，精通 ADB、世界银行和 AfDB 采购规程。"
    "请从招标文件中提取投标提交要求的详细信息。"
)

EXTRACTION_PROMPT = """请从以下招标文件内容中提取所有投标提交要求。

=== 招标文件摘录 ===
{bid_context}

请以 JSON 格式返回:
{{
  "submission_format": {{
    "method": "online|physical|both",
    "online_platform": "平台名称或 URL (如有)",
    "physical_address": "提交地址 (如有)"
  }},
  "copies": {{
    "original": 1,
    "copies": 0,
    "electronic_copies": 0,
    "format_requirements": "PDF/Word/其他"
  }},
  "language": {{
    "primary": "English",
    "translation_required": false,
    "certified_translation": false
  }},
  "bid_security": {{
    "required": true,
    "amount": "金额或百分比",
    "currency": "USD",
    "form": "bank_guarantee|demand_draft|bid_bond",
    "validity_days": 0
  }},
  "required_documents": [
    {{
      "document": "文件名称",
      "mandatory": true,
      "format": "original|copy|notarized",
      "notes": "备注"
    }}
  ],
  "packaging_instructions": "密封和标记要求",
  "late_submission_policy": "迟交政策"
}}
"""


class ExtractSubmission(Skill):
    """Extract submission format, copies, and required documents."""

    name = "extract_submission"
    description = "提取投标提交格式、份数、语言和必交文件清单"

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
                max_tokens=3000,
            )
            return SkillResult(
                success=True,
                data=result,
                tokens_consumed=0,
            )
        except Exception as e:
            return SkillResult(success=False, error=str(e))
