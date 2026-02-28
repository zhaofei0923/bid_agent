"""WB (World Bank) analysis prompt templates (V2 addition)."""

WB_QUALIFICATION_PROMPT = """请分析以下世界银行招标文件内容，提取投标人资格要求。

## 招标文件上下文
{bid_document_context}

## 世界银行采购指南参考
{knowledge_context}

世界银行特有注意事项：
- 关注《采购规定》(Procurement Regulations) 中的合格资格要求
- 注意 ESF (环境社会框架) 合规要求
- 检查是否有国别限制或制裁名单要求
- 识别世界银行反欺诈反腐败 (ACGF) 声明要求

输出 JSON:
{{
  "legal": [...],
  "financial": [...],
  "technical": [...],
  "personnel": [...],
  "esf_requirements": [...],
  "sanctions_compliance": {{"declaration_required": bool}},
  "jv_requirements": {{"allowed": bool, "lead_partner_share": "xx%", "max_members": n}}
}}"""


WB_EVALUATION_CRITERIA_PROMPT = """请分析以下世界银行招标文件内容，提取评审标准。

## 招标文件上下文
{bid_document_context}

## 世界银行采购指南参考
{knowledge_context}

世界银行评标方法说明：
- QCBS: 质量和费用综合评标法 (最常见)
- QBS: 质量评标法 (复杂咨询项目)
- FBS: 固定预算评标法
- LCS: 最低费用评标法
- CQS: 基于咨询人资质的遴选

输出 JSON:
{{
  "method": "QCBS",
  "weights": {{"technical": 80, "financial": 20}},
  "technical_criteria": [
    {{
      "criterion": "Specific Experience",
      "weight": 30,
      "sub_criteria": [...]
    }}
  ],
  "minimum_technical_score": 75,
  "financial_formula": "Sf = 100 × Fm / F",
  "wb_specific": {{
    "procurement_method": "ICB|NCB|RFP",
    "review_type": "prior|post"
  }}
}}"""
