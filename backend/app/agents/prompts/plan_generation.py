"""Bid plan generation prompt templates.

Generates structured, institution-aware bid preparation task plans based on
ADB Procurement Policy 2017 and WB Procurement Regulations 7th Edition.
Tasks use the 8-category system and dates are reverse-scheduled from the
submission deadline.
"""

# ── 8 Category Definitions (shared constant) ─────────────────────
VALID_CATEGORIES = (
    "documents",
    "team",
    "technical",
    "experience",
    "financial",
    "compliance",
    "submission",
    "review",
)

PLAN_GENERATION_SYSTEM_PROMPT = (
    "你是拥有 20 年国际多边机构投标管理经验的资深项目经理，精通以下采购规程：\n"
    "• ADB: Procurement Policy (2017)、Procurement Regulations (2017, as amended)、"
    "Standard Bidding Documents (SBDs) 全系列 (Consulting Firm / Individual / Goods / Works)\n"
    "• WB: Procurement Regulations for IPF Borrowers (7th Ed, Sep 2025)、"
    "Standard Procurement Documents (SPDs)、Procurement Strategy for Development (PPSD)\n\n"
    "你的工作原则：\n"
    "1. 所有任务必须从截标日期(submission_deadline)【倒推】安排，而非从今日往后排\n"
    "2. 任务必须覆盖 8 个类别：documents / team / technical / experience / financial / compliance / submission / review\n"
    "3. 每条任务需关联招标文件的具体条款（如 ITB 4.2、Section III、ELI‑1 等）\n"
    "4. ADB 项目需关注 SBD 标准表格名（ELI-1/FIN-1/TECH-1 等）\n"
    "5. WB 项目需关注 SPD Section 结构（Section I-VI）和 ESF 合规要求\n"
    "6. 生成 15-25 条任务，每个类别至少 1 条，格式统一\n"
    "7. 直接输出 JSON，不要加解释文字"
)

PLAN_GENERATION_PROMPT = """根据以下招标分析结果，生成一份投标准备任务清单。

## 项目机构
{institution}

## 截标期限
{deadline}

## 关键日期
{key_dates}

## 资质要求
{qualification_requirements}

## 评审标准
{evaluation_criteria}

## 提交要求
{submission_checklist}

## 商务条款
{commercial_terms}

## 风险评估
{risk_assessment}

{institution_template}

---

### 生成规则

**时间倒推法**（从截标日期往前推算，以下为参考范围）：
- **review** (内审签章)：截标前 0-1 天
- **submission** (提交准备)：截标前 1-3 天
- **compliance** (合规检查)：截标前 3-5 天
- **financial** (财务商务)：截标前 5-7 天
- **technical** (技术方案) + **experience** (业绩整理)：截标前 7-14 天
- **team** (团队组建)：截标前 10-14 天
- **documents** (资质证书)：截标前 14-21 天

如截标日期未知，则 due_date 全部返回 null。

**8 个任务类别**（每个至少 1 条）：
- **documents**: 公司资质证书、营业执照、法人授权书、注册证明
- **team**: 项目经理任命、技术专家组建、简历更新、资质证书确认
- **technical**: 技术方案撰写、工作计划、方法论、HSE 方案
- **experience**: 类似项目业绩筛选、合同金额/规模证明、业主推荐信
- **financial**: 报价编制、财务报表审计、银行保函申请、预算测算
- **compliance**: 合规声明、反腐败声明、投标保函、格式合规检查
- **submission**: 文件打印装订、翻译公证、电子/物理提交、快递安排
- **review**: 内部交叉审查、管理层签批、最终合规检查、签章确认

**优先级规则**：
- **high**: 截标关键路径 — 资质证明、银行保函、投标保函、技术方案核心部分
- **medium**: 核心内容 — 人员简历、报价表、项目业绩、工作计划
- **low**: 收尾工作 — 格式检查、文件装订、归档

请以 JSON 格式返回（15-25 条任务）：
{{
  "plan_summary": "计划整体说明（100-200字，概述投标策略和关键路径）",
  "tasks": [
    {{
      "title": "任务标题（简明，不超过 50 字）",
      "description": "任务详情（50-150 字，说明具体要做什么、参考哪个条款/评分标准、关键注意事项）",
      "category": "documents|team|technical|experience|financial|compliance|submission|review",
      "priority": "high|medium|low",
      "start_date": "YYYY-MM-DD（任务开始日期）或 null",
      "due_date": "YYYY-MM-DD（任务截止日期）或 null",
      "sort_order": 1,
      "related_document": "关联招标文件条款（如 ITB 4.2、Section III、ELI-1）或 null",
      "reference_page": null
    }}
  ]
}}

注意：
1. sort_order 从 1 开始递增，按建议执行顺序排列（最先执行的 = 1）
2. 直接输出 JSON，不要包含任何解释文字
"""

# ── Institution-specific few-shot templates ───────────────────────

ADB_PLAN_TEMPLATE = """
### ADB 投标计划参考框架（基于 SBD 标准）
ADB 咨询服务项目通常需提交以下核心文件，请据此生成任务：
- **ELI-1/ELI-2**: 资格声明表（法人资格、联合体情况）
- **FIN-1/FIN-2/FIN-3**: 财务状况表（营业额、流动性、财务能力声明）
- **TECH-1**: 技术建议书封面
- **TECH-2**: 组织与经验（公司简介、类似项目）
- **TECH-3**: 对 TOR 的理解与建议方法论、工作计划
- **TECH-4**: 团队组成与任务分工
- **TECH-5**: 工作进度表
- **TECH-6**: 关键人员简历
- **FIN-1 (Financial)**: 财务建议书汇总
- 投标保函 (Bid Security) / 履约保函 (Performance Security)
- 反腐败声明、制裁声明
"""

WB_PLAN_TEMPLATE = """
### WB 投标计划参考框架（基于 SPD 标准）
世界银行项目通常参照 SPD 目录结构，请据此生成任务：
- **Section I**: 投标邀请函 → 确认投标资格、截止要求
- **Section II**: 投标人须知 (ITB) + 投标资料表 (BDS) → 逐条对照检查
- **Section III**: 评审标准与资质要求 → 技术/财务评分准备
- **Section IV**: 投标表格 → 填写标准表格（资格声明、财务报表等）
- **Section V**: 合同条件 + 特殊条件 → 审查商务条款风险
- **Section VI**: 技术规范/TOR → 撰写技术方案
- **ESF 合规**: 环境社会框架要求 → E&S 管理计划、劳工管理方案
- **PPSD (采购策略)**: 了解采购方法 (QCBS/QBS/FBS/LCS/ICB/NCB)
- 禁止名单检查、反腐败声明、利益冲突声明
"""
