"""Bid plan generation prompt templates."""

PLAN_GENERATION_SYSTEM_PROMPT = (
    "你是专业的多边发展银行投标项目管理专家，精通 ADB、世界银行等国际采购规程。"
    "你的任务是根据招标分析结果，为投标团队生成一份结构清晰、可落地执行的投标任务清单。"
    "任务需按照重要性和时间顺序排列，覆盖合规、技术、商务、行政四个维度。"
)

PLAN_GENERATION_PROMPT = """根据以下招标分析结果，生成一份完整的投标准备任务清单。

## 招标分析摘要
{analysis_summary}

## 截标期限
{deadline}

## 项目机构
{institution}

---

请生成 10-20 条具体可执行的投标准备任务，覆盖以下四个类别：
- **compliance** (合规类)：资质文件准备、证书核实、合规声明等
- **technical** (技术类)：技术方案撰写、人员简历准备、类似项目业绩整理等
- **commercial** (商务类)：报价单编制、财务报表准备、银行保函申请等
- **administrative** (行政类)：文件打印装订、翻译公证、快递寄送等

每条任务的截止日期请根据截标期限往前推算合理时间（如截标前 3 天、7 天、14 天等）。
若截标期限未知，due_date 返回 null。

请以 JSON 格式返回：
{{
  "tasks": [
    {{
      "title": "任务标题（简明，不超过 50 字）",
      "description": "任务详情说明（50-150 字，说明做什么、参考哪个评分标准、关键注意事项）",
      "category": "compliance|technical|commercial|administrative",
      "priority": "high|medium|low",
      "due_date": "YYYY-MM-DD 或 null",
      "sort_order": 1
    }}
  ],
  "plan_summary": "本投标准备计划的整体说明（100-200字）"
}}

注意：
1. sort_order 从 1 开始递增，按建议执行顺序排列
2. 高优先级（high）任务：截标关键路径上的任务，如资质证明、价格表、银行保函
3. 中优先级（medium）：技术方案、人员配置等核心内容
4. 低优先级（low）：格式检查、文件归档等收尾工作
5. 直接输出 JSON，不要包含任何解释文字
"""
