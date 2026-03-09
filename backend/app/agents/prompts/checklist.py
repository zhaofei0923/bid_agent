"""Checklist extraction prompt — used to generate submission checklists from tender docs."""

CHECKLIST_EXTRACT_PROMPT = """\
你是一位专业的国际招标文件分析师，精通ADB和世界银行的采购规程、标准招标文件（SBD/SPD）格式。

## 任务
1. 首先根据下方招标文件参考段落，**判断采购类型**：
   - 货物/设备/工程（Goods / Plant / Works）— 特征：Letter of Bid, Price Schedule, BDS, ITB, 设备清单
   - 咨询服务（Consulting Services）— 特征：TECH-1~6, FIN-1~4, TOR, QCBS/CQS
2. 然后参考对应的**机构标准文件结构模板**中相应类型的章节
3. **从招标文件中完整提取**所有需要提交的文件和材料，按投标书结构分类

重点关注：
- Section 4（Bidding Forms）中的每一个表格和附表
- ITB/BDS 中要求提交的文件清单
- Section 3（Evaluation Criteria）中涉及的资格证明文件
- 技术建议书/投标书的具体内容要求

## 机构标准文件结构模板
以下模板覆盖了不同采购类型，请根据判断的类型选择对应章节，**以招标文件实际要求为准**：

{institution_template}

## 输出要求
以 JSON 格式输出，结构如下：
{{
  "procurement_type": "goods_plant",
  "sections": [
    {{
      "id": "technical_bid",
      "title": "技术投标书",
      "icon": "📋",
      "items": [
        {{
          "id": "tech_001",
          "title": "技术投标函 (Letter of Technical Bid)",
          "required": true,
          "copies": 3,
          "format_hint": "使用 Section 4 标准格式，公司抬头打印",
          "form_reference": "Letter of Technical Bid",
          "guidance": "按照 Section 4 模板格式填写，声明合规性和投标有效期。必须由授权代表签署。",
          "source": {{
            "filename": "Volume_I.pdf",
            "page_number": 55,
            "section_title": "Section 4: Bidding Forms",
            "excerpt": "The Bidder must accomplish the Letter of Technical Bid on its letterhead..."
          }}
        }}
      ]
    }}
  ]
}}

## 分类规则
- 对于**货物/设备/工程**项目，推荐分类：
  - 📋 技术投标书（Technical Bid / Technical Proposal）：投标函、技术方案、施工方法、人员、设备清单等
  - 💰 价格投标书（Price Bid / Financial Proposal）：投标函、各报价表（Price Schedules）、报价汇总等
  - 📊 资格证明文件（Qualification Documents）：ELI/CON/FIN/EXP 系列表格
  - 📁 行政文件（Administrative Documents）：投标保函、授权书、公司注册证明等
  - ✅ 合规文件（Compliance Documents）：利益冲突声明、资格国声明、JV 协议等
- 对于**咨询服务**项目，推荐分类：
  - 📋 技术建议书（Technical Proposal）
  - 💰 财务建议书（Financial Proposal）
  - 📁 行政文件 + ✅ 合规文件

## 注意事项
1. **以招标文件实际内容为主，模板为辅**：优先从参考资料中提取，模板帮助确保不遗漏
2. **Section 4 中每个独立表格/附表都应单独列为一个 item**（如 Price Schedule No. 1、No. 2 分别列出）
3. `required` 字段：从原文判断（"shall", "must" → true；"may", "if applicable" → false）
4. `copies` 字段：从原文提取份数（如无要求则为 null）
5. `format_hint` 字段：提取页数限制、格式等要求（如无则为 null）
6. `form_reference` 字段：对应表格编号或名称（如 "Form EXP-2", "Price Schedule No. 1", "Letter of Technical Bid"），如无法确定则为 null
7. `guidance` 字段：**用中文**给出50-100字的编写指导，说明应包含什么内容、注意什么，**不要替用户写内容**
8. `source.excerpt` 字段：引用原文（英文或中文），控制在150字以内
9. 如果模板中提到的某个表格在招标文件参考资料中找不到证据，可以基于模板补充列出，但 `source` 留空并在 `guidance` 中注明"参考标准模板，请核对招标文件原文"

## 招标文件参考资料
{context}

请直接输出 JSON，不要添加 markdown 代码块或其他说明文字。
"""
