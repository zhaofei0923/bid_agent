"""ExecutiveSummary — project overview and quick Bid/No-Bid signal."""

from app.agents.skills.base import Skill, SkillContext, SkillResult

SYSTEM_PROMPT = (
    "你是专业的多边发展银行投标分析师，精通 ADB、世界银行和 AfDB 采购规程。"
    "请从招标文件中提取项目概览信息，帮助投标经理在30秒内判断项目价值。"
)

EXTRACTION_PROMPT = """请从以下招标文件内容中提取项目概览信息。

=== 招标文件摘录 ===
{bid_context}

=== 参考知识 ===
{kb_context}

请以 JSON 格式返回:
{{
  "project_name": "项目名称（中英文）",
  "country_region": "国家/地区",
  "borrower_agency": "借款方/采购机构",
  "funding_source": "资金来源（ADB Loan/Grant编号）",
  "estimated_budget": "预估预算金额及货币",
  "procurement_method": {{
    "type": "ICB|NCB|QCBS|QBS|FBS|LCS|CQS|Shopping|Direct",
    "full_name": "完整名称",
    "brief_description": "该采购方式简要说明（50字以内）"
  }},
  "contract_type": "Goods|Works|Consulting Services|Non-Consulting Services",
  "industry_sector": "行业领域（如交通、能源、水务、ICT等）",
  "lot_info": {{
    "has_lots": false,
    "lot_count": 0,
    "lot_descriptions": []
  }},
  "project_scope_summary": "项目范围一句话概述（100字以内）",
  "quick_assessment": {{
    "attractiveness": "high|medium|low",
    "rationale": "快速评估理由（2-3句话）",
    "key_considerations": ["关键考量因素1", "关键考量因素2"]
  }}
}}
"""


class ExecutiveSummary(Skill):
    """Extract project overview for quick assessment."""

    name = "executive_summary"
    description = "提取项目概览信息，帮助快速判断投标价值"

    async def execute(self, ctx: SkillContext) -> SkillResult:
        bid_context = ctx.parameters.get("bid_context", "")
        kb_context = ctx.parameters.get("kb_context", "")

        if not bid_context:
            return SkillResult(
                success=False,
                error="No bid context provided",
            )

        prompt = EXTRACTION_PROMPT.format(
            bid_context=bid_context,
            kb_context=kb_context,
        )

        try:
            result = await ctx.llm_client.extract_json(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.2,
                max_tokens=2000,
            )
            return SkillResult(
                success=True,
                data=result.data,
                tokens_consumed=result.tokens_used,
            )
        except Exception as e:
            return SkillResult(success=False, error=str(e))
