"""Guidance prompt templates — used by SectionGuidance and review skills."""

SECTION_GUIDANCE_PROMPT = """你是一位投标编制顾问。请为用户提供以下章节的编写指导。

## 章节信息
- 章节名称: {section_title}
- 评分权重: {scoring_weight} 分（满分 100）
- 评分子项: {sub_criteria}

## 招标文件要求
{bid_requirements}

## 相关知识库参考
{knowledge_context}

请提供：
1. **内容框架** — 建议的小节结构和每部分字数建议
2. **得分要点** — 评委关注的核心得分点
3. **格式要求** — 页数、图表、附件等格式规范
4. **关键用词** — 应出现的专业术语和关键词
5. **常见错误** — 避免的常见问题
6. **示范要素** — 每个小节应包含的关键要素示范

⚠️ 你的指导应帮助用户自己编写，不要直接生成内容。

输出 JSON:
{{
  "content_outline": [
    {{"subsection": "标题", "description": "内容提示", "suggested_length": "X页"}}
  ],
  "scoring_tips": [...],
  "format_requirements": {{...}},
  "key_terms": [...],
  "common_mistakes": [...],
  "reference_samples": [...]
}}"""


REVIEW_DRAFT_PROMPT = """请审查以下用户编写的标书章节草稿。

## 章节: {section_title}
## 评分标准
{evaluation_criteria}

## 招标文件要求
{bid_requirements}

## 用户草稿
{user_draft}

请从以下4个维度评审：

1. **格式合规** (15分) — 符合格式、页数、装订要求
2. **内容完整** (35分) — 覆盖所有要求的内容要点
3. **评分对齐** (35分) — 精准命中评分标准给分点
4. **语言质量** (15分) — 专业性、逻辑性、表达准确性

输出 JSON:
{{
  "dimensions": [
    {{
      "name": "format_compliance",
      "score": 12,
      "max_score": 15,
      "issues": ["具体问题描述"],
      "suggestions": ["具体改进建议"]
    }}
  ],
  "total_score": 78,
  "max_score": 100,
  "priority_improvements": [
    {{
      "priority": "high",
      "issue": "问题描述",
      "suggestion": "修改建议",
      "expected_score_gain": 5
    }}
  ],
  "overall_feedback": "总体评价"
}}"""


QUALITY_REVIEW_FULL_PROMPT = """请对以下完整投标文件进行全面质量审查。

## 招标文件要求摘要
{bid_requirements}

## 评分标准
{evaluation_criteria}

## 投标文件内容
{proposal_content}

请从以下 4 个维度进行全面审查：

### 1. 完整性 (25%)
- 所有章节是否齐全
- 各章节内容是否完整覆盖要求
- 附件、证明文件是否齐全

### 2. 合规性 (25%)
- 格式是否符合规定（页数、字体、装订）
- 是否包含所有必需的表格和声明
- 签章是否完整

### 3. 一致性 (25%)
- 文挡内部数据是否一致
- 技术方案与工作计划是否匹配
- 人员安排与时间表是否协调

### 4. 竞争力 (25%)
- 关键评分项是否有充分亮点
- 是否有差异化竞争优势
- 预估得分与竞争力分析

输出 JSON:
{{
  "completeness": {{"score": 85, "issues": [...], "missing_items": [...]}},
  "compliance": {{"score": 90, "issues": [...]}},
  "consistency": {{"score": 80, "issues": [...], "conflicts": [...]}},
  "competitiveness": {{"score": 75, "strengths": [...], "weaknesses": [...]}},
  "overall_score": 82,
  "win_probability": "medium",
  "critical_improvements": [
    {{"area": "...", "issue": "...", "recommendation": "...", "impact": "high"}}
  ]
}}"""


QUALITY_REVIEW_QUICK_PROMPT = """请对以下投标文件进行快速审查（重点检查关键问题）。

## 核心要求
{core_requirements}

## 投标文件摘要
{proposal_summary}

快速检查:
1. 是否有遗漏的必选章节
2. 是否有明显的格式违规
3. 关键数据是否一致
4. 是否有致命性的合规问题

输出 JSON:
{{
  "pass": true|false,
  "critical_issues": [...],
  "warnings": [...],
  "quick_score": 85
}}"""
