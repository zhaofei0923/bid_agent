"""ReviewDraft — review user-written draft against bid requirements."""

from app.agents.skills.base import Skill, SkillContext, SkillResult

SYSTEM_PROMPT = (
    "你是专业的投标文件审查专家。请审查用户编写的草稿，"
    "从格式合规性、内容完整性、评分对标、语言质量四个维度评分，"
    "并给出具体的改进建议。以 JSON 格式返回。"
)

REVIEW_PROMPT = """请审查以下投标文件章节草稿。

=== 章节要求 ===
{section_requirements}

=== 用户草稿 ===
{draft_content}

=== 评分标准参考 ===
{scoring_context}

请以 JSON 格式返回:
{{
  "overall_score": 0-100,
  "format_compliance": {{"score": 0-100, "issues": ["..."]}},
  "content_completeness": {{"score": 0-100, "missing_points": ["..."]}},
  "scoring_alignment": {{"score": 0-100, "suggestions": ["..."]}},
  "language_quality": {{"score": 0-100, "improvements": ["..."]}},
  "specific_feedback": ["反馈1", "反馈2"],
  "priority_improvements": ["优先改进1", "优先改进2"]
}}
"""


class ReviewDraft(Skill):
    """Review user draft against bid requirements."""

    name = "review_draft"
    description = "审查用户草稿并提供修改建议"

    async def execute(self, ctx: SkillContext) -> SkillResult:
        draft_content = ctx.parameters.get("draft_content", "")
        section_requirements = ctx.parameters.get("section_requirements", "")
        scoring_context = ctx.parameters.get("scoring_context", "")

        if not draft_content:
            return SkillResult(success=False, error="No draft content")

        try:
            result = await ctx.llm_client.extract_json(
                prompt=REVIEW_PROMPT.format(
                    section_requirements=section_requirements,
                    draft_content=draft_content,
                    scoring_context=scoring_context,
                ),
                system_prompt=SYSTEM_PROMPT,
                temperature=0.2,
                max_tokens=4000,
            )
            return SkillResult(success=True, data=result.data, tokens_consumed=result.tokens_used)
        except Exception as exc:
            return SkillResult(success=False, error=str(exc))
