# BidAgent V2 — 产品需求规格 (PRD)

> 版本: 2.0.0 | 日期: 2026-02-11 | 状态: Draft

## 1. 产品概述

### 1.1 产品定位

BidAgent 是面向多边发展银行（ADB/WB/UN）投标场景的 AI Agent 平台。帮助咨询公司和企业完成从**招标信息发现**到**投标文件编制**的全流程工作，AI 提供专业指导而非直接生成文档。

### 1.2 核心价值

| 价值 | 说明 |
|------|------|
| 效率提升 | AI 全程指导标书编制，将 2-4 周人工编写缩短至 3-5 天 |
| 质量保障 | AI 多维度质量审查，降低废标风险 |
| 知识复用 | 机构采购准则知识库 + 历史标书经验沉淀 |
| 智能决策 | Bid/No-Bid 决策支持，评标预测 |

### 1.3 目标用户

| 角色 | 描述 | 核心需求 |
|------|------|---------|
| 投标经理 | 负责投标决策和整体协调 | 快速评估投标可行性，掌控投标进度 |
| 技术提案撰写人 | 编写技术方案、团队简历 | AI 指导编写符合格式要求的提案章节 |
| 商务人员 | 负责定价和商务条款 | 了解评分标准，优化报价策略 |
| 管理员 | 平台管理 | 用户管理、系统统计、积分管理 |

---

## 2. 用户使用流程

### 2.1 核心工作流

```
发现招标 → 评估决策 → 文档解析 → AI 分析 → 计划制定 → AI 指导编制 → 质量审查 → 提交
```

### 2.2 详细流程

#### Phase 1: 发现与评估
1. **浏览招标信息** — 系统自动爬取 ADB/WB/UN 招标公告，提供搜索、筛选、分页
2. **创建投标项目** — 从招标信息一键创建项目，或手动创建
3. **Bid/No-Bid 分析** — AI 快速评估投标可行性，给出建议

#### Phase 2: 文档理解
4. **上传招标文件** — 支持 PDF/DOCX，自动解析、OCR、章节识别
5. **AI 文档解读** — 8 维度深度分析：资质要求、评分标准、关键日期、BDS 修改、提交要求、评标方法、商务条款、风险评估
6. **智能问答** — 基于招标文件的 RAG 问答，实时解答投标疑问

#### Phase 3: 标书编制指导
7. **投标计划** — AI 生成投标待办清单，含截止日期、优先级、负责人
8. **编制指导** — 用户在问答区提出需求，系统智能路由：简单问题 → prompt 回答，复杂需求 → Skills 分析
9. **逐章指导** — AI 针对每个章节提供编写指导（格式要求、内容要点、模板参考、评分对标），用户自行编写
10. **质量审查** — 对用户编写的内容进行 4 维度审查（完整性/合规性/一致性/风险）+ 改进建议

#### Phase 4: 管理
11. **积分系统** — 按使用量消费积分，支持充值套餐
12. **项目管理** — 项目列表、状态跟踪、收藏
13. **知识库管理** — 机构采购准则、历史模板的上传与管理

---

## 3. 功能模块与优先级

### P0 — MVP 核心（必须实现）

| 模块 | 功能 | 说明 |
|------|------|------|
| **用户系统** | 注册/登录/JWT 认证 | 邮箱 + 密码，HS256 JWT |
| **招标爬虫** | ADB + WB + UNGM 三源爬取 | 定时爬取 + 手动触发，Cloudflare 绕过 |
| **招标浏览** | 搜索/筛选/分页/详情 | 全文搜索，多条件组合筛选 |
| **项目管理** | CRUD + 状态流转 | draft → analyzing → guiding → review → submitted |
| **文档上传** | PDF/DOCX 上传与解析 | SHA256 去重，OCR（PaddleOCR），章节自动识别 |
| **文档向量化** | 分块 + Embedding + pgvector | 1024 维，余弦相似度 |
| **招标分析** | 8 步 RAG 增强分析 | 资质/评分/日期/BDS/提交/评标方法/商务条款/风险 |
| **智能问答** | 招标文件 RAG QA | 检索相关分块 → LLM 生成答案 |
| **标书编制指导** | AI 问答式指导 | 智能路由 Q&A → 逐章编写指导 → 用户自行编写 → AI 审查反馈 |
| **质量审查** | 4 维度 AI 审查 | 完整性 + 合规性 + 一致性 + 风险识别 |
| **知识库** | 机构准则 RAG | ADB/WB 采购准则上传、向量搜索、跨库检索 |
| **国际化** | 中/英双语 | next-intl，所有 UI 文本走翻译文件 |
| **MCP Server** | 工具化知识检索 | Agent 按需调用 Tool 替代硬编码 RAG |
| **Skills 系统** | 封装固定分析流程 | 资质分析/评分提取/编制指导/质量审查等 Skill |
| **投标计划** | AI 生成待办清单 | P0 简化版：8 类任务，从 deadline 反推日期 |

### P1 — 增强功能（V2 后续迭代）

| 模块 | 功能 | 说明 |
|------|------|------|
| **评标预测** | 分数预测 + 薄弱环节分析 | 技术/商务/综合分 + 胜率 + SWOT |
| **统计仪表盘** | 运营/用户/财务统计 | 管理员专属 |
| **积分支付** | 充值套餐 + 支付宝/微信 | 积分扣减，交易记录 |
| **翻译服务** | 中英文档翻译 | 腾讯云翻译 API |

### P2 — 远期功能

| 模块 | 功能 | 说明 |
|------|------|------|
| **专家库** | 专家管理 + 技能标签 | 自动匹配项目需求 |
| **预算估算** | 人天费率 + 报价计算 | 单价库 + AI 辅助估算 |
| **团队组建** | 项目团队配置 | 基于技能需求自动推荐 |
| **密码重置** | 忘记密码流程 | 邮件验证码 |
| **文件云存储** | MinIO/S3 | 替代本地文件系统 |
| **多 LLM Provider** | 支持 OpenAI/Claude 切换 | 抽象 LLM 层 |

---

## 4. 功能详细规格

### 4.1 用户系统

**注册**:
- 字段: email (唯一), password (≥8 字符), name
- 密码: bcrypt 哈希存储
- 注册后自动登录，返回 JWT

**登录**:
- 邮箱 + 密码认证
- 返回: access_token (30min) + refresh_token (7d)
- 支持 token 刷新

**用户模型字段**:
| 字段 | 类型 | 说明 |
|------|------|------|
| email | string, unique | 登录邮箱 |
| name | string | 显示名 |
| company | string? | 公司名 |
| avatar_url | string? | 头像 |
| role | enum(user, admin) | 角色 |
| language | string, default "zh" | 语言偏好 |
| credits_balance | int, default 0 | 积分余额 |

### 4.2 招标爬虫

**数据源**:

| 源 | 目标 URL | 反爬措施 | 更新频率 |
|---|---|---|---|
| ADB | `www.adb.org/projects/tenders` | Cloudflare Bypass (DrissionPage) | 每日 |
| WB | `www.worldbank.org/en/business-opportunities` | httpx + 速率限制 3s | 每日 |
| UNGM | `www.ungm.org/PublicNotice` | httpx | 每日 |

**统一数据模型** (TenderInfo):
| 字段 | 说明 |
|------|------|
| source | adb / wb / un |
| external_id | 源站唯一 ID |
| title | 标题 |
| url | 原始链接 |
| project_number | 项目编号 |
| description | 描述 |
| country | 国家 |
| sector | 行业 |
| status | 状态 (active/closed/awarded) |
| deadline | 截止日期 |
| published_date | 发布日期 |
| estimated_value | 估计金额 |
| procurement_type | 采购类型 |
| documents | 附件 URL 列表 |

**ADB 分类映射**:
- 组别: goods (货物), consulting (咨询)
- 类型: 投标邀请/采购公告/意向征集/咨询任务
- 状态: active/closed/awarded/archived

**UNGM 支持机构**: UNDP, UNICEF, WHO, ILO, FAO, WFP, UNIDO, ITU, UNOPS, UN Women 等 14 个

### 4.3 文档处理

**支持格式**: PDF (.pdf), Word (.docx)

**处理管线**:
```
上传 → 去重(SHA256) → 解析(PyMuPDF/python-docx) → 扫描件检测 → OCR(PaddleOCR) → 章节识别 → 分块(1000/200) → 向量化(Embedding) → 存储(pgvector)
```

**扫描件检测阈值**:
- 文字密度 < 50 字符/页 → 判定为扫描件
- 文字占比 < 1% → 判定为扫描件

**OCR 配置**: PaddleOCR, 语言=中英, CPU 模式, 角度分类启用, 缩放 2x

**分块参数**:
| 参数 | 默认值 |
|------|--------|
| chunk_size | 1000 字符 |
| chunk_overlap | 200 字符 |
| min_chunk_size | 100 字符 |

**章节自动识别** (ADB SBD 标准结构):
| Section | 类型 |
|---------|------|
| Section 1 | ITB — 投标须知 |
| Section 2 | BDS — 投标数据表 |
| Section 3 | Qualification — 资格标准 |
| Section 4 | Forms — 投标表格 |
| Section 5 | Countries — 合格国家 |
| Part 2 | Requirements — 需求说明 |
| Part 3 | Contract — 合同条件 |

### 4.4 招标分析（8 步）

每步均为 RAG 增强：**检索招标文件分块 + 检索知识库参考 → 拼接 prompt → LLM(temperature=0.2, max_tokens=4000) → JSON 解析存储**

| 步骤 | 分析维度 | 核心输出 |
|------|---------|---------|
| 1 | 资质要求 | 4 类资质(法律/财务/技术/经验) + JV 要求 + 国内优惠 |
| 2 | 评分标准 | 评标方法(QCBS/QBS/FBS/LCS) + 分项权重 + 及格线 |
| 3 | 关键日期 | 截止日/开标/澄清/有效期/投前会/工期 |
| 4 | 提交要求 | 格式/份数/语言/保函/必交文件清单 |
| 5 | BDS 修改 | 逐条列出 BDS 对 ITB 的修改 + 优先级 + 影响 |
| 6 | 评标方法 | 详细评分尺度 + 淘汰条件 + 策略建议 |
| 7 | 商务条款 | 付款(里程碑) + 保函(4 类) + 保修 + 违约金 + 保险 + 争议解决 |
| 8 | 风险评估 | 5 维风险(资质/技术/商务/时间/合规) + Bid/No-Bid 建议 + 行动项 |

### 4.5 标书编制指导工作流

**核心理念**: AI 不直接生成标书文档，而是作为专业投标顾问，指导用户按招标文件要求和规范自行编写。用户通过问答区与系统交互，系统智能判断路由方式。

**交互模式**:
```
用户在问答区提问 → 系统意图识别 → 简单问题: prompt 直接回答
                                  → 复杂需求: 调用 Skills 分析后回答
                                  → 章节指导: 提供格式要求 + 内容要点 + 模板参考 + 评分对标
                                  → 内容审查: 审查用户草稿 + 给出修改建议
```

**智能路由规则**:
| 用户意图 | 路由方式 | 示例 |
|---------|---------|------|
| 一般性问题 | Prompt 直接回答 | "这个项目的截止日期是？" |
| 格式规范查询 | RAG 检索 + Prompt | "技术方案需要什么格式？" |
| 章节编写指导 | Skills (SectionGuidance) | "请指导我写技术方案章节" |
| 评分标准对标 | Skills (EvaluateCriteria) | "我的经验描述能否满足评分要求？" |
| 草稿内容审查 | Skills (ReviewDraft) | "请审查我写的团队配置章节" |
| 合规性检查 | Skills (QualityReview) | "检查我的投标文件是否完整合规" |

**默认评分权重**: Technical Approach 40%, Team 30%, Experience 20%, Management 10%

### 4.6 质量审查

对用户编写的投标文件内容进行 AI 审查，提供改进建议。

| 维度 | 检查内容 |
|------|---------|
| 完整性 | 必需章节覆盖率，附件齐全性 |
| 合规性 | 格式规范，签名要求，截止日期 |
| 一致性 | 团队信息前后一致，预算与工作计划匹配，时间线合理 |
| 风险识别 | 资质证书有效期，项目经验匹配度，ADB 经验 |

支持两种模式：完整审查 + 快速检查

### 4.7 投标工作台 UI

**7 步流程导航**:
| # | 步骤 | 说明 |
|---|------|------|
| 1 | 上传招标文件 | 拖拽上传，实时进度 |
| 2 | 招标文件解读 | AI 分析结果展示 + 文档结构浏览 |
| 3 | 投标资格审核 | 资质匹配度分析 |
| 4 | 生成投标计划 | 任务清单 + 甘特图 |
| 5 | AI 编制指导 | 问答式指导 + 用户编写 |
| 6 | 审核要点核对 | 质量审查 + 对照检查 |
| 7 | 完成投标文件 | 用户完成编写 + 导出最终文档 |

**机构差异化流程描述**:
- ADB: 文档上传 → TOR 分析 → 公司简介 → 团队组建 → 技术方案 → 工作计划 → 预算编制 → 审核提交
- WB: 文档上传 → 需求分析 → 资质证明 → 技术建议书 → 财务建议书 → 审核提交
- UN: 文档上传 → RFP 分析 → 供应商信息 → 技术响应 → 价格响应 → 合规声明 → 审核提交

### 4.8 积分系统

| 操作 | 消费 |
|------|------|
| 搜索浏览招标信息 | 免费 |
| 创建投标项目 | 10 积分 |
| AI 编制指导 | 20-100 积分（按对话次数） |
| AI 分析 | 按 Token 消耗计费 |

---

## 5. 非功能需求

### 5.1 性能

| 指标 | 目标 |
|------|------|
| 页面首屏加载 | < 2s |
| API 响应时间（非 LLM） | < 500ms (P95) |
| 文档解析（100 页 PDF） | < 60s |
| 向量搜索 | < 200ms |
| LLM 单步分析 | < 30s |
| 并发用户 | 100+ |

### 5.2 安全

- JWT 认证 (HS256, 30min 过期)
- 密码 bcrypt 哈希
- CORS 白名单
- API 速率限制（滑动窗口）
- 文件上传大小限制 + 类型校验
- SQL 注入防护（SQLAlchemy ORM）

### 5.3 可用性

- Docker Compose 一键部署
- 数据库连接池 + 健康检查
- Redis 不可用时降级到 BackgroundTasks
- Embedding Provider 自动降级（混元 → 智谱）
- LLM 调用失败时 rule-based fallback

### 5.4 国际化

- 支持语言: 中文 (zh), 英文 (en)
- 框架: next-intl
- 所有 UI 文本必须走翻译文件，禁止硬编码

---

## 6. 与 V1 的关键差异

| 方面 | V1 现状 | V2 目标 |
|------|---------|---------|
| Agent 框架 | MiniMax 遗留 → DeepSeek + LangGraph | DeepSeek + LangGraph + MCP/Skills |
| 数据库 ID | UUID 与 String(36) 混用 | 统一 UUID |
| 数据模型 | 双 Opportunity 模型冗余 | 统一为单一 Opportunity |
| 爬虫基类 | 两个不同 BaseCrawler | 统一基类 |
| 迁移管理 | 手工 SQL 文件 (顺序混乱) | Alembic 版本化迁移 |
| 前端 UI 库 | 文档写 shadcn 但未安装 | 实际安装并使用 shadcn/ui |
| 前端 Service 层 | 仅 1 个 service 文件 | 完整 API 客户端层 |
| 知识库 RAG | 硬编码 Service 调用 | MCP Tool 化，Agent 自主检索 |
| 支付配置 | 模型存在但配置缺失 | 完整支付配置 + 环境变量 |
| 测试覆盖 | 约 7 个测试文件 | 目标 80%+ 覆盖率 |
| datetime | `datetime.utcnow()` (已弃用) | `datetime.now(UTC)` |
| 工作流状态 | 内存字典存储 | Redis 持久化 |

---

## 附录 A: 术语表

| 术语 | 说明 |
|------|------|
| ADB | Asian Development Bank — 亚洲开发银行 |
| WB | World Bank — 世界银行 |
| UN / UNGM | United Nations Global Marketplace — 联合国全球市场 |
| TOR | Terms of Reference — 任务大纲 |
| RFP | Request for Proposal — 征求建议书 |
| ITB | Instructions to Bidders — 投标须知 |
| BDS | Bid Data Sheet — 投标数据表 |
| SBD | Standard Bidding Documents — 标准招标文件 |
| QCBS | Quality and Cost Based Selection — 质量与费用综合评估 |
| QBS | Quality Based Selection — 质量评估 |
| FBS | Fixed Budget Selection — 固定预算评估 |
| LCS | Least Cost Selection — 最低费用评估 |
| JV | Joint Venture — 联合体 |
| MCP | Model Context Protocol — 模型上下文协议 |
| RAG | Retrieval-Augmented Generation — 检索增强生成 |
| pgvector | PostgreSQL 向量搜索扩展 |
