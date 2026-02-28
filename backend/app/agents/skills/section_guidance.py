"""SectionGuidance — provide writing guidance for a specific bid section."""

from app.agents.llm_client import Message
from app.agents.skills.base import Skill, SkillContext, SkillResult

SYSTEM_PROMPT = (
    "你是专业的投标顾问。你的任务是为用户提供标书章节的编写指导。"
    "请提供详细、实操性强的指导意见，帮助用户自己完成高质量的章节编写。"
    "不要直接替用户写内容，而是指导他们如何写。"
)

GUIDANCE_PROMPT = """请为以下投标文件章节提供编写指导。

=== 章节信息 ===
标题: {section_title}
目标字数: {word_count_target}
评分权重: {scoring_weight}%

=== 招标文件相关内容 ===
{bid_context}

=== 参考模板 ===
{template_context}

请提供以下结构化指导:
1. 章节格式要求和结构建议
2. 必须涵盖的核心内容要点
3. 如何与评分标准对标
4. 常见错误和注意事项
5. 参考建议和最佳实践
"""


class SectionGuidance(Skill):
    """Provide writing guidance for a specific proposal section."""

    name = "section_guidance"
    description = "提供章节编写指导"

    async def execute(self, ctx: SkillContext) -> SkillResult:
        section_config = ctx.parameters.get("section_config", {})
        bid_context = ctx.parameters.get("bid_context", "")
        template_context = ctx.parameters.get("template_context", "")

        if not section_config:
            return SkillResult(success=False, error="No section config")

        try:
            response = await ctx.llm_client.chat(
                messages=[
                    Message("system", SYSTEM_PROMPT),
                    Message(
                        "user",
                        GUIDANCE_PROMPT.format(
                            section_title=section_config.get("title", ""),
                            word_count_target=section_config.get("word_count_target", "N/A"),
                            scoring_weight=section_config.get("scoring_weight", "N/A"),
                            bid_context=bid_context,
                            template_context=template_context,
                        ),
                    ),
                ],
                temperature=0.3,
                max_tokens=4000,
            )

            return SkillResult(
                success=True,
                data={
                    "section_id": section_config.get("id"),
                    "guidance": response.content,
                    "format_requirements": section_config.get("format_requirements", ""),
                    "content_outline": section_config.get("key_points", []),
                    "scoring_alignment": section_config.get("linked_criteria", []),
                },
                tokens_consumed=response.usage.get("total_tokens", 0),
            )
        except Exception as exc:
            return SkillResult(success=False, error=str(exc))
