"""QualityReview — full quality review of proposal document."""

from app.agents.skills.base import Skill, SkillContext, SkillResult

SYSTEM_PROMPT = (
    "你是资深投标审查专家。请对提交的投标文件进行全面质量审查，"
    "从完整性、合规性、一致性、风险四个维度进行评分和分析。以 JSON 返回。"
)

FULL_REVIEW_PROMPT = """请对以下投标文件进行全面质量审查。

=== 投标要求摘要 ===
{bid_requirements}

=== 投标文件内容 ===
{proposal_content}

请以 JSON 格式返回:
{{
  "completeness": {{
    "score": 0-100,
    "missing_sections": ["..."],
    "missing_attachments": ["..."]
  }},
  "compliance": {{
    "score": 0-100,
    "issues": ["..."]
  }},
  "consistency": {{
    "score": 0-100,
    "issues": ["..."]
  }},
  "risks": {{
    "score": 0-100,
    "items": ["..."]
  }},
  "overall_score": 0-100,
  "win_probability": "high|medium|low",
  "critical_improvements": ["..."]
}}
"""

QUICK_REVIEW_PROMPT = """请快速审查以下内容，给出简要反馈:

{proposal_content}

返回JSON: {{"score": 0-100, "key_issues": ["..."], "quick_suggestions": ["..."]}}
"""


class QualityReview(Skill):
    """Full or quick quality review of proposal."""

    name = "quality_review"
    description = "投标文件质量审查"

    async def execute(self, ctx: SkillContext) -> SkillResult:
        mode = ctx.parameters.get("mode", "full")
        proposal_content = ctx.parameters.get("proposal_content", "")
        bid_requirements = ctx.parameters.get("bid_requirements", "")

        if not proposal_content:
            return SkillResult(success=False, error="No proposal content")

        try:
            if mode == "quick":
                result = await ctx.llm_client.extract_json(
                    prompt=QUICK_REVIEW_PROMPT.format(
                        proposal_content=proposal_content
                    ),
                    system_prompt=SYSTEM_PROMPT,
                    temperature=0.1,
                    max_tokens=500,
                )
            else:
                result = await ctx.llm_client.extract_json(
                    prompt=FULL_REVIEW_PROMPT.format(
                        bid_requirements=bid_requirements,
                        proposal_content=proposal_content,
                    ),
                    system_prompt=SYSTEM_PROMPT,
                    temperature=0.2,
                    max_tokens=4000,
                )
            return SkillResult(success=True, data=result.data, tokens_consumed=result.tokens_used)
        except Exception as exc:
            return SkillResult(success=False, error=str(exc))
