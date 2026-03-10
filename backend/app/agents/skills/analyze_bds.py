"""AnalyzeBDS — analyze Bid Data Sheet modifications to standard provisions."""

from app.agents.skills.base import Skill, SkillContext, SkillResult

SYSTEM_PROMPT = (
    "你是专业的多边发展银行投标分析师，精通 ADB Standard Bidding Documents。"
    "请逐条分析 BDS (Bid Data Sheet) 对 ITB (Instructions to Bidders) "
    "标准条款的修改。对每一条 BDS 给出: ITB 原条款号 → 标准内容摘要 → "
    "BDS 修改内容 → 修改影响分析 → 投标人行动项。"
)

ANALYSIS_PROMPT = """请逐条分析以下 BDS (Bid Data Sheet) 的内容，对每条 BDS 引用的 ITB 标准条款进行对照解读。

=== BDS 内容 ===
{bid_context}

=== ITB 标准条款参考 (知识库) ===
{kb_context}

分析要求:
1. 对每一条 BDS 引用的 ITB 条款号，找出标准条款原文含义
2. 分析 BDS 对该标准条款做了什么修改或补充
3. 评估该修改对投标人的影响程度
4. 给出投标人需要采取的具体行动

请以 JSON 格式返回:
{{
  "bds_modifications": [
    {{
      "bds_reference": "BDS x",
      "itb_clause": "ITB x.x",
      "itb_standard_content": "ITB 标准条款原文摘要（如知识库中有则引用，否则标注'标准条款待核实'）",
      "bds_modification": "BDS 具体修改/补充内容",
      "change_type": "override|supplement|specify|restrict|waive",
      "priority": "critical|high|medium|low",
      "impact_analysis": "对投标人的影响详细说明",
      "action_required": "投标人需要采取的具体行动",
      "compliance_note": "合规注意事项"
    }}
  ],
  "critical_changes_summary": "关键修改概述（按重要程度排列的关键变化）",
  "compliance_checklist": [
    {{
      "item": "需满足的合规要求",
      "bds_reference": "BDS x / ITB x.x",
      "status": "must_comply",
      "difficulty": "easy|moderate|challenging"
    }}
  ],
  "statistics": {{
    "total_bds_items": 0,
    "critical_count": 0,
    "high_count": 0,
    "medium_count": 0,
    "low_count": 0
  }}
}}
"""


class AnalyzeBDS(Skill):
    """Analyze BDS modifications to standard ITB provisions."""

    name = "analyze_bds"
    description = "分析 BDS 对标准条款的修改及其对投标人的影响"

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
