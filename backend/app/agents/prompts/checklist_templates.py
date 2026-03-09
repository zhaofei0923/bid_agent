"""Institution-specific standard bidding document structure templates.

These constants inject ADB/WB standard bid document frameworks into the
checklist extraction prompt so the LLM has a reference skeleton.
The LLM should still extract actual requirements from the uploaded tender
documents — these templates only serve as structural guidance.
"""

ADB_CHECKLIST_TEMPLATE = """\
### ADB 标准招标文件（SBD）投标文件结构参考

ADB 咨询服务类项目通常遵循以下 Section 4 标准投标表格体系：

**一、技术建议书（Technical Proposal）**
- **TECH-1**: 技术建议书提交表（Technical Proposal Submission Form）
- **TECH-2**: 咨询公司组织与经验（Consultant's Organization and Experience）
  - TECH-2A: 公司基本情况（Consultant's General Information）
  - TECH-2B: 类似项目经验（Similar Assignment Experience）
- **TECH-3**: 对 TOR 的理解、方法论与工作计划（Comments/Suggestions on TOR, Approach & Methodology, Work Plan）
- **TECH-4**: 团队组成与任务分工（Team Composition and Task Assignments）
- **TECH-5**: 工作进度表（Work Schedule）
- **TECH-6**: 关键专家简历（Curriculum Vitae for Proposed Key Experts）— 每人一份

**二、财务建议书（Financial Proposal）**
- **FIN-1**: 财务建议书提交表（Financial Proposal Submission Form）
- **FIN-2**: 费用汇总表（Summary of Costs）
- **FIN-3**: 报酬明细表（Remuneration）
- **FIN-4**: 可报销费用明细表（Reimbursable Expenses）

**三、资格声明（Eligibility & Qualification）**
- **ELI-1**: 咨询公司资格声明表（Consultant's Eligibility Declaration）
- **ELI-2**: 联合体/合作伙伴信息表（JV/Association Information if applicable）
- **FIN-1 (Qualification)**: 财务状况声明（Financial Situation — Revenue/Liquidity/Net Worth）
- **FIN-2 (Qualification)**: 平均年营业额（Average Annual Turnover）

**四、行政文件（Administrative Documents）**
- 授权代表声明书（Power of Attorney / Authorization Letter）
- 投标保函（Bid Security / Bid-Securing Declaration）— 如 BDS 要求
- 公司注册证明文件副本
- 反腐败与不行贿声明（Anti-Corruption Declaration）

**五、合规文件（Compliance Documents）**
- 利益冲突声明（Conflict of Interest Declaration）
- 符合性声明书（Compliance with Eligible Countries — Section 5）
- 联合体协议书（JV Agreement）— 如适用
- 投标有效期确认

**注意事项**
- Section 4 表格编号在不同 SBD 版本中可能略有差异，以实际招标文件为准
- BDS（Bid Data Sheet, Section 2）可能对标准 ITB 条款做了项目特定修改
- 关键评分标准通常在 Section 3（Evaluation and Qualification Criteria）
"""

WB_CHECKLIST_TEMPLATE = """\
### 世界银行（WB）标准采购文件（SPD）投标文件结构参考

WB 咨询服务类项目通常遵循以下 SPD Section 结构：

**一、技术建议书（Section III — Technical Proposal）**
- **Form TECH-1**: 技术建议书提交函（Technical Proposal Submission Form）
- **Form TECH-2**: 咨询公司组织与经验
  - 2A: 公司概况（Consultant's Organization）
  - 2B: 类似经验（Consultant's Experience）
- **Form TECH-3**: 对 TOR 的理解与建议方法论、工作计划
  - 技术方案（Technical Approach and Methodology）
  - 工作计划（Work Plan）
  - 人员安排（Staffing Schedule）
- **Form TECH-4**: 团队组成、任务分配与工时估算
- **Form TECH-5**: 工作进度与活动计划（Work Schedule）
- **Form TECH-6**: 关键专家简历（每人一份，含学历、工作经历、类似项目经验、语言能力）

**二、财务建议书（Section IV — Financial Proposal）**
- **Form FIN-1**: 财务建议书提交函（Financial Proposal Submission Form）
- **Form FIN-2**: 费用汇总表（Summary of Costs）
- **Form FIN-3**: 报酬明细（Breakdown of Remuneration）
- **Form FIN-4**: 可报销费用明细（Reimbursable Expenses）

**三、资格与合格性文件（Section II — Qualification）**
- 公司注册与法人证明
- 最近 3-5 年审计财务报表
- 平均年营业额证明
- 类似项目合同业绩证明
- ESF（环境与社会框架）合规声明

**四、行政文件**
- 投标书签署授权书（Power of Attorney）
- 投标保函 / 投标保证声明（Bid-Securing Declaration）— 如 Data Sheet 要求
- 联合体协议书（JV Agreement）— 如适用
- 反欺诈与反腐败承诺书（Fraud and Corruption Declaration）

**五、合规文件**
- WB 制裁名单合规声明（WB Sanctions List Compliance）
- 利益冲突声明（Conflict of Interest）
- ESF 劳工管理程序（Labor Management Procedures）— 如适用
- 环境与社会承诺书（Environmental and Social Commitment Plan）— 如适用

**注意事项**
- WB Procurement Regulations for IPF Borrowers (7th Edition, Sep 2025) 为最新版
- Data Sheet（投标资料表）对标准条款的项目特定修改具有最高优先级
- PPSD（Project Procurement Strategy for Development）决定选择方式（QCBS/CQS/FBS/LCS/SSS）
- ESF（Environmental and Social Framework）合规要求是 WB 项目特有的关注重点
"""


def get_institution_template(institution: str) -> str:
    """Return the checklist template for the given institution."""
    if institution == "wb":
        return WB_CHECKLIST_TEMPLATE
    # Default to ADB for "adb" and any other value
    return ADB_CHECKLIST_TEMPLATE
