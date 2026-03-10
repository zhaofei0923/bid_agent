"""BuildComplianceMatrix — consolidated mandatory requirements compliance matrix."""

from app.agents.skills.base import Skill, SkillContext, SkillResult

SYSTEM_PROMPT = (
    "你是专业的多边发展银行投标合规分析师。"
    "请基于前序分析结果，汇总所有强制性要求，生成统一的合规检查矩阵，"
    "帮助投标团队确保不遗漏任何必须满足的要求。"
)

MATRIX_PROMPT = """请基于以下分析结果，汇总所有强制性/必须满足的要求，生成合规检查矩阵。

=== 资质要求分析 ===
{qualification_summary}

=== 提交要求分析 ===
{submission_summary}

=== BDS 分析 ===
{bds_summary}

=== 技术要求分析 ===
{technical_summary}

=== 招标文件补充 ===
{bid_context}

请以 JSON 格式返回:
{{
  "compliance_items": [
    {{
      "id": 1,
      "source": "ITB|BDS|TOR|Section 3|Section 4",
      "reference": "具体条款编号",
      "requirement": "要求内容摘要",
      "type": "mandatory|scoring|recommended",
      "category": "qualification|technical|financial|administrative|legal",
      "difficulty": "easy|moderate|challenging",
      "action_required": "投标人需要采取的行动",
      "evidence_needed": "需要提供的证明文件",
      "deadline_relevance": "与时间相关的要求说明（如适用）"
    }}
  ],
  "go_no_go_checklist": [
    {{
      "item": "Go/No-Go 关键检查项",
      "source_reference": "来源",
      "is_showstopper": true,
      "assessment_guidance": "如何评判是否满足"
    }}
  ],
  "summary": {{
    "total_mandatory": 0,
    "total_scoring": 0,
    "critical_items_count": 0,
    "overall_compliance_risk": "low|medium|high",
    "key_attention_areas": ["需重点关注的领域"]
  }}
}}
"""


class BuildComplianceMatrix(Skill):
    """Build consolidated compliance matrix from all analysis dimensions."""

    name = "compliance_matrix"
    description = "构建合规检查矩阵，汇总所有强制性要求"

    async def execute(self, ctx: SkillContext) -> SkillResult:
        bid_context = ctx.parameters.get("bid_context", "")
        qualification_summary = ctx.parameters.get("qualification_summary", "未分析")
        submission_summary = ctx.parameters.get("submission_summary", "未分析")
        bds_summary = ctx.parameters.get("bds_summary", "未分析")
        technical_summary = ctx.parameters.get("technical_summary", "未分析")

        prompt = MATRIX_PROMPT.format(
            qualification_summary=qualification_summary,
            submission_summary=submission_summary,
            bds_summary=bds_summary,
            technical_summary=technical_summary,
            bid_context=bid_context,
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
