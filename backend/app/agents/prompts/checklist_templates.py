"""Institution-specific standard bidding document structure templates.

These constants inject ADB/WB standard bid document frameworks into the
checklist extraction prompt so the LLM has a reference skeleton.
The LLM should still extract actual requirements from the uploaded tender
documents — these templates only serve as structural guidance.

Each institution has TWO template sections:
  - Consulting Services (CSRN / SPD-CS)
  - Goods, Plant & Works (SBD-Goods / SPD-Goods)
The LLM must first identify which procurement type applies.
"""

ADB_CHECKLIST_TEMPLATE = """\
### ADB 标准招标文件（SBD）投标文件结构参考

请先根据招标文件内容判断采购类型，再参考对应的模板。

---

#### 类型 A：ADB 货物/设备/工程采购（Goods / Plant / Works — Single-Stage Two-Envelope）

此类 SBD 的 Section 4（Bidding Forms）通常包含以下标准表格：

**一、投标函件（Bid Submission Letters）**
- **Letter of Technical Bid**: 技术投标书（声明合规性、投标有效期、Bid-Securing Declaration 等）
- **Letter of Price Bid**: 价格投标书（报价汇总、折扣声明、货币说明等）

**二、报价表（Price Schedules）**
- **Schedule No. 1**: 从国外供应的设备及强制备件（Plant & Mandatory Spare Parts Supplied from Abroad）
- **Schedule No. 2**: 从业主国供应的设备及强制备件（Plant & Mandatory Spare Parts from Within Country）
- **Schedule No. 3**: 设计服务（Design Services）
- **Schedule No. 4**: 安装及其他服务（Installation and Other Services）
- **Schedule No. 5**: 大修/年度保养（Grand Summary / Recurrent Costs）
- **Schedule No. 6**: 推荐备件（Recommended Spare Parts）— 如适用
- 注：具体 Schedule 编号和数量因文件不同而异

**三、资格声明表格（Qualification Forms — Section 4 后半部分）**
- **Form ELI-1**: 投标人资格声明（Bidder's Eligibility — Individual or JV）
- **Form ELI-2**: 联合体信息表（JV Information）— 如适用
- **Form CON-1**: 历史合同不履行/诉讼记录（Historical Contract Non-Performance）
- **Form CON-2**: 待决诉讼或仲裁（Pending Litigation / Arbitration）
- **Form FIN-1**: 财务状况声明（Historical Financial Performance）
- **Form FIN-2**: 平均年营业额（Average Annual Turnover）
- **Form FIN-3**: 财务资源可用性（Availability of Financial Resources）
- **Form FIN-4**: 当前合同承诺（Current Contract Commitments）
- **Form EXP-1**: 一般经验（General Experience）
- **Form EXP-2**: 类似合同经验（Specific Experience — similar contracts）

**四、技术建议书内容（Technical Proposal — 通常 ITB 17 条要求）**
- 施工方案 / 工作方法说明（Method Statement / Work Plan）
- 项目进度计划（Project Schedule / Bar Chart）
- 拟用关键人员简历（Key Personnel CVs）— 项目经理、技术专家等
- 拟用设备清单（Equipment Schedule）
- 环境健康安全管理计划（EHS Management Plan）
- 分包商方案（Subcontracting Arrangements）— 如适用
- 制造商授权书（Manufacturer's Authorization）— 如适用

**五、行政文件（Administrative Documents）**
- 投标保函（Bid Security）或 投标保证声明（Bid-Securing Declaration）
- 签署授权书（Power of Attorney）
- 公司注册证明
- 反腐败声明（Integrity / Anti-Corruption Declaration）

**六、合规文件（Compliance Documents）**
- 资格国声明（Eligible Countries — Section 5）
- 利益冲突声明（Conflict of Interest Declaration）
- 联合体协议（JV Agreement）— 如适用
- 投标有效期确认

---

#### 类型 B：ADB 咨询服务（Consulting Services — CSRN/RFP）

**一、技术建议书（Technical Proposal — Section 4 Forms）**
- **TECH-1**: 技术建议书提交表
- **TECH-2**: 咨询公司组织与经验（TECH-2A 公司概况 + TECH-2B 类似项目经验）
- **TECH-3**: 方法论与工作计划
- **TECH-4**: 团队组成与任务分工
- **TECH-5**: 工作进度表
- **TECH-6**: 关键专家简历（每人一份）

**二、财务建议书（Financial Proposal）**
- **FIN-1**: 财务建议书提交表
- **FIN-2**: 费用汇总表
- **FIN-3**: 报酬明细表
- **FIN-4**: 可报销费用明细表

**三、资格/行政/合规文件**
- ELI-1/ELI-2 资格声明、授权书、投标保函、反腐败声明等

---

**通用注意事项**
- Section 4 表格编号因 SBD 版本不同可能有差异，以实际招标文件为准
- BDS（Bid Data Sheet, Section 2）对 ITB 条款的修改具有最高优先级
- Section 3（Evaluation and Qualification Criteria）包含评标标准和资格要求
"""

WB_CHECKLIST_TEMPLATE = """\
### 世界银行（WB）标准采购文件（SPD）投标文件结构参考

请先根据招标文件内容判断采购类型，再参考对应的模板。

---

#### 类型 A：WB 货物/设备/工程采购（Goods / Plant / Works）

**一、投标函件（Bid Submission Forms）**
- **Letter of Bid**: 投标书（含报价汇总、合规声明、有效期确认）
- **Letter of Technical Bid**: 技术投标书（Two-Envelope 方式时）
- **Letter of Price Bid**: 价格投标书（Two-Envelope 方式时）

**二、报价表（Price Schedules）**
- **Price Schedule for Goods**: 货物报价表（国外供货 + 国内供货）
- **Price Schedule for Related Services**: 相关服务报价表
- **Price Schedule for Plant & Installation**: 设备及安装报价表（Plant 类项目）
- **Grand Summary**: 报价汇总表

**三、资格表格（Qualification Forms）**
- **Form ELI**: 资格声明（Eligibility Declaration）
- **Form CON**: 历史合同履行记录 + 待决诉讼
- **Form FIN**: 财务能力（Historical Financial Performance, Annual Turnover, Financial Resources）
- **Form EXP**: 经验证明（General Experience + Specific/Similar Contract Experience）

**四、技术建议书（Technical Proposal — 如适用）**
- 施工/供货方案、进度计划
- 关键人员简历
- 设备清单
- 制造商授权书
- 环境与社会管理计划（ESMP）

**五、行政/合规文件**
- 投标保函（Bid Security / Bid-Securing Declaration）
- 签署授权书（Power of Attorney）
- 反欺诈与反腐败声明（Fraud and Corruption Declaration）
- WB 制裁名单合规声明
- ESF 合规文件（Environmental and Social Framework）— 如适用

---

#### 类型 B：WB 咨询服务（Consulting Services — SPD-CS）

**一、技术建议书**
- **Form TECH-1 ~ TECH-6**（同 ADB 咨询服务结构，表格编号类似）

**二、财务建议书**
- **Form FIN-1 ~ FIN-4**

**三、资格/行政/合规文件**
- 公司注册证明、财务报表、授权书、ESF 合规声明等

---

**通用注意事项**
- Data Sheet 对标准条款的项目特定修改具有最高优先级
- PPSD 决定选择方式（QCBS/CQS/FBS/LCS/SSS）
- ESF 合规要求是 WB 项目的特有关注重点
"""


def get_institution_template(institution: str) -> str:
    """Return the checklist template for the given institution."""
    if institution == "wb":
        return WB_CHECKLIST_TEMPLATE
    # Default to ADB for "adb" and any other value
    return ADB_CHECKLIST_TEMPLATE
