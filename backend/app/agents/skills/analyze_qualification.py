"""AnalyzeQualification — extract qualification requirements from bid documents."""

from app.agents.skills.base import Skill, SkillContext, SkillResult

SYSTEM_PROMPT = (
    "你是专业的多边发展银行投标分析师，精通 ADB、世界银行和 AfDB 采购规程。"
    "请从招标文件中提取资质要求，并以 JSON 格式返回结构化结果。"
)

EXTRACTION_PROMPT = """请从以下招标文件内容中提取所有资质要求。

=== 招标文件摘录 ===
{bid_context}

=== 参考知识 ===
{kb_context}

请以 JSON 格式返回:
{{
  "qualification_requirements": [
    {{
      "category": "Legal|Financial|Technical|Experience",
      "requirements": ["requirement 1", "..."],
      "evidence_required": ["证据 1", "..."],
      "source_reference": "ITB x.x"
    }}
  ],
  "joint_venture_requirements": {{
    "allowed": true/false,
    "max_members": n,
    "lead_partner_min_share": "percentage"
  }},
  "domestic_preference": {{
    "applicable": true/false,
    "margin": "percentage or null"
  }}
}}
"""


class AnalyzeQualification(Skill):
    """Extract qualification requirements from bid documents."""

    name = "analyze_qualification"
    description = "分析招标文件中的资质要求"

    async def execute(self, ctx: SkillContext) -> SkillResult:
        # Context is retrieved upstream by the pipeline via RAG (build_analysis_context).
        bid_context = ctx.parameters.get("bid_context", "")
        kb_context = ctx.parameters.get("kb_context", "")

        if not bid_context:
            return SkillResult(
                success=False,
                error="No bid document context provided",
            )

        try:
            result = await ctx.llm_client.extract_json(
                prompt=EXTRACTION_PROMPT.format(
                    bid_context=bid_context,
                    kb_context=kb_context,
                ),
                system_prompt=SYSTEM_PROMPT,
                temperature=0.2,
                max_tokens=4000,
            )

            return SkillResult(
                success=True,
                data=result.data,
                tokens_consumed=result.tokens_used,
            )
        except Exception as exc:
            return SkillResult(success=False, error=str(exc))
