"""AnalyzeTechnical — deep technical requirements analysis from TOR/SOW."""

from app.agents.skills.base import Skill, SkillContext, SkillResult

SYSTEM_PROMPT = (
    "你是专业的多边发展银行投标分析师，擅长技术规范和工作范围分析。"
    "请从招标文件中深度分析技术要求、交付物、人员配置等核心信息，"
    "帮助投标团队快速理解项目技术实质。"
)

ANALYSIS_PROMPT = """请深入分析以下招标文件中的技术要求部分。

=== 招标文件摘录 (TOR/SOW/技术规范) ===
{bid_context}

=== 参考知识 ===
{kb_context}

请以 JSON 格式返回:
{{
  "project_scope": {{
    "objective": "项目目标概述",
    "scope_summary": "工作范围总结（200字以内）",
    "geographic_coverage": "项目地理覆盖范围",
    "implementation_period": "实施周期"
  }},
  "deliverables": [
    {{
      "name": "交付物名称",
      "description": "交付物描述",
      "deadline": "交付时间要求",
      "acceptance_criteria": "验收标准（如有）"
    }}
  ],
  "technical_standards": [
    {{
      "standard": "必须遵循的技术标准/规范名称",
      "description": "标准简要说明",
      "source_reference": "文件引用位置"
    }}
  ],
  "system_requirements": [
    {{
      "category": "设备|软件|基础设施|其他",
      "requirement": "具体要求",
      "specification": "技术规格",
      "mandatory": true
    }}
  ],
  "key_personnel": [
    {{
      "position": "职位名称",
      "qualifications": "资质要求",
      "experience_years": "经验年限要求",
      "man_months": "人月数（如有）",
      "evaluation_weight": "该岗位评分权重（如有）"
    }}
  ],
  "risk_areas": [
    {{
      "area": "技术风险领域",
      "description": "风险描述",
      "impact": "high|medium|low",
      "suggested_mitigation": "建议应对措施"
    }}
  ],
  "clarification_needed": [
    {{
      "item": "需澄清的技术问题",
      "reason": "为何需要澄清",
      "suggested_question": "建议向采购方提出的问题"
    }}
  ]
}}
"""


class AnalyzeTechnical(Skill):
    """Deep analysis of technical requirements from TOR/SOW."""

    name = "analyze_technical"
    description = "深度分析技术规范、工作范围、交付物和人员要求"

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
