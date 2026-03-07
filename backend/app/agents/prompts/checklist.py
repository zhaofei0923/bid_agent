"""Checklist extraction prompt — used to generate submission checklists from tender docs."""

CHECKLIST_EXTRACT_PROMPT = """\
你是一位专业的国际招标文件分析师，熟悉ADB、世界银行、AfDB的采购规程和标准招标文件格式。

## 任务
请仔细阅读下方提供的招标文件参考段落，**完整提取**所有需要提交的文件和材料，按照投标书结构分类整理。

## 输出要求
以 JSON 格式输出，结构如下：
{{
  "sections": [
    {{
      "id": "technical_proposal",
      "title": "技术建议书",
      "icon": "📋",
      "items": [
        {{
          "id": "tech_001",
          "title": "技术方案",
          "required": true,
          "copies": 3,
          "format_hint": "不超过50页，A4纸，12号字体",
          "guidance": "详细说明项目实施方法、时间计划、团队安排，必须覆盖招标文件Section 4中列明的所有评分点，突出团队过往类似项目经验",
          "source": {{
            "filename": "RFP_Section8.pdf",
            "page_number": 45,
            "section_title": "Section 8.2 – Documents Required",
            "excerpt": "The Technical Proposal shall include..."
          }}
        }}
      ]
    }}
  ]
}}

## 分类参考（根据实际文件调整）
常见分类包括：
- 📋 技术建议书（Technical Proposal）：技术方案、资质证明、人员简历、类似项目经验等
- 💰 财务建议书（Financial Proposal）：报价表、资金证明、定价明细等
- 📁 行政文件（Administrative Documents）：投标保函、公司注册证明、授权书、不行贿声明等
- ✅ 合规文件（Compliance Documents）：利益冲突声明、资格预审文件等

## 注意事项
1. **只根据提供的参考资料提取**，不要凭空添加
2. `required` 字段：从原文判断是否为强制要求（"shall", "must" → true；"may", "if applicable" → false）
3. `copies` 字段：从原文提取所需份数（如无要求则为 null）
4. `format_hint` 字段：提取页数限制、字体、格式等要求（如无则为 null）
5. `guidance` 字段：**用中文**给出50-100字的编写指导，说明应包含什么内容、注意什么，**不要替用户写内容**
6. `source.excerpt` 字段：引用招标文件原文（英文或中文均可），控制在150字以内
7. 如果参考资料不足以提取完整清单，在能提取的范围内尽量完整

## 招标文件参考资料
{context}

请直接输出 JSON，不要添加 markdown 代码块或其他说明文字。
"""
