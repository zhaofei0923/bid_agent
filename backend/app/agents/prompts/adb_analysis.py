"""ADB-specific analysis prompt templates.

Template variables use {curly_braces} for str.format() substitution.
"""

QUALIFICATION_EXTRACTION_PROMPT = """请分析以下招标文件内容，提取投标人资格要求。

## 招标文件上下文
{bid_document_context}

## ADB 采购指南参考
{knowledge_context}

请提取并结构化以下信息：
1. **法律资格** — 法人资格、营业执照、注册地要求
2. **财务要求** — 最低年营业额、流动比率、净资产要求
3. **技术能力** — 类似项目经验年限、规模、数量要求
4. **人员要求** — 关键人员资质、学历、经验年限
5. **联合体** — 是否允许联合体、主成员要求、成员数上限
6. **国内优惠** — 是否适用国内投标人优惠

输出 JSON:
{{
  "legal": [...],
  "financial": [...],
  "technical": [...],
  "personnel": [...],
  "jv_requirements": {{"allowed": bool, "lead_partner_share": "xx%", "max_members": n}},
  "domestic_preference": {{"applicable": bool, "margin": "x%"}}
}}"""


EVALUATION_CRITERIA_PROMPT = """请分析以下招标文件内容，提取评审标准和评分方法。

## 招标文件上下文
{bid_document_context}

## ADB 采购指南参考
{knowledge_context}

请提取：
1. **评标方法** — QCBS/QBS/FBS/LCS，技术财务权重
2. **技术评审标准** — 各评审维度、权重、子项及分值
3. **最低技术得分** — 通过技术评审的最低分数线
4. **财务评分公式** — 最低分法/公式法

输出 JSON:
{{
  "method": "QCBS",
  "weights": {{"technical": 80, "financial": 20}},
  "technical_criteria": [
    {{
      "criterion": "相关经验",
      "weight": 30,
      "sub_criteria": [
        {{"item": "类似项目数量", "max_score": 15}},
        {{"item": "项目规模", "max_score": 15}}
      ]
    }}
  ],
  "minimum_technical_score": 75,
  "financial_formula": "Sf = 100 × Fm / F"
}}"""


KEY_DATES_PROMPT = """请从以下招标文件中提取关键日期和时间表。

## 招标文件上下文
{bid_document_context}

## ADB 采购指南参考
{knowledge_context}

请提取：
1. 投标截止日期和时间（含时区）
2. 标前会日期和地点
3. 澄清截止日期
4. 开标日期
5. 投标有效期
6. 合同签订预计时间
7. 项目开始/结束日期

输出 JSON:
{{
  "submission_deadline": {{"date": "YYYY-MM-DD", "time": "HH:MM", "timezone": "UTC+X"}},
  "pre_bid_conference": {{"date": "YYYY-MM-DD", "mandatory": bool}},
  "clarification_deadline": "YYYY-MM-DD",
  "bid_opening": "YYYY-MM-DD",
  "validity_period": "X days",
  "contract_signing": "YYYY-MM-DD (estimated)",
  "project_start": "YYYY-MM-DD",
  "project_end": "YYYY-MM-DD"
}}"""


BDS_MODIFICATION_PROMPT = """请分析以下 BDS（Bid Data Sheet / 投标数据表）的内容，识别对标准条款(ITB)的修改。

## 招标文件上下文
{bid_document_context}

## ADB 采购指南参考
{knowledge_context}

对于每个 BDS 条款：
1. 标明对应的 ITB 标准条款编号
2. 说明修改内容
3. 标注对投标准备的影响程度（高/中/低）
4. 给出投标注意事项

输出 JSON:
{{
  "modifications": [
    {{
      "bds_clause": "BDS X.X",
      "itb_reference": "ITB X.X",
      "modification": "修改内容描述",
      "impact": "high|medium|low",
      "bidder_action": "投标人应注意..."
    }}
  ],
  "summary": "BDS 整体影响摘要"
}}"""


SUBMISSION_REQUIREMENTS_PROMPT = """请从以下招标文件中提取投标提交要求。

## 招标文件上下文
{bid_document_context}

## ADB 采购指南参考
{knowledge_context}

请提取：
1. 提交方式（电子/纸质/两者）
2. 份数要求（正本/副本数量）
3. 装订和包装要求
4. 投标保证金要求
5. 签署和授权要求
6. 文件格式和语言要求

输出 JSON:
{{
  "submission_method": "electronic|physical|both",
  "copies": {{"original": 1, "copies": 3}},
  "packaging": "分册装订要求描述",
  "bid_security": {{"required": bool, "amount": "USD X", "form": "bank guarantee"}},
  "signing": "法定代表人或授权代理人签署",
  "format": {{"language": "English", "page_limit": "50 pages", "font": "12pt"}}
}}"""


COMMERCIAL_TERMS_PROMPT = """请分析以下招标文件中的商务条款。

## 招标文件上下文
{bid_document_context}

## ADB 采购指南参考
{knowledge_context}

请提取：
1. 付款条款（预付款比例、里程碑付款、尾款）
2. 履约保证金
3. 保险要求
4. 违约罚则
5. 知识产权条款
6. 税务条款

输出 JSON:
{{
  "payment_terms": {{
    "advance_payment": "XX%",
    "milestone_payments": [...],
    "retention": "XX%"
  }},
  "performance_security": {{"required": bool, "percentage": "X%", "form": "bank guarantee"}},
  "insurance": [...],
  "penalties": {{"delay_penalty": "X% per week, max Y%"}},
  "ip_rights": "描述",
  "tax": "描述"
}}"""


RISK_ASSESSMENT_PROMPT = """请基于以下分析结果，进行综合风险评估。

## 资格要求分析
{qualification}

## 评分标准分析
{criteria}

## 关键日期
{dates}

## BDS 修改
{bds}

## ADB 采购指南参考
{kb_context}

请评估：
1. **合规风险** — 资格条件不满足的风险
2. **时间风险** — 准备时间是否充裕
3. **竞争风险** — 评分标准对我方是否有利
4. **商务风险** — 合同条款中的不利因素
5. **技术风险** — 技术方案可行性风险

输出 JSON:
{{
  "overall_risk_level": "high|medium|low",
  "risks": [
    {{
      "category": "compliance",
      "description": "风险描述",
      "likelihood": "high|medium|low",
      "impact": "high|medium|low",
      "mitigation": "建议的缓解措施"
    }}
  ],
  "recommendation": "投标/不投标建议及理由",
  "confidence_score": 0.75
}}"""
