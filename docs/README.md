# BidAgent 开发文档

> 多边机构投标AI Agent Web平台 - 帮助用户完成ADB、WB、UN等机构的投标工作

[![Next.js](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red)]()

---

# 📖 文档使用指南

本指南帮助你快速理解和使用 BidAgent 开发文档体系。

## 🗺️ 文档地图

```
docs/
├── README.md ◀── 你在这里 (入口 + 使用指南)
│
├── 📐 architecture/           # 架构设计 (理解系统)
│   ├── system-overview.md     → 技术栈、模块划分、部署架构
│   ├── data-model.md          → 数据库表结构、关系、索引
│   └── agent-workflow.md      → LangGraph状态机、节点设计
│
├── 📡 api-contracts/          # API契约 (前后端对接)
│   └── openapi.yaml           → 所有REST API定义
│
├── 📋 task-specs/             # 任务规格书 (开发执行)
│   ├── M0-infrastructure/     → 基础设施 (8任务)
│   ├── M1-user-system/        → 用户系统 (10任务)
│   ├── M2-crawler/            → 爬虫模块 (8任务)
│   ├── M3-llm-service/        → LLM服务 (10任务)
│   ├── M4-document-processing/→ 文档处理 (10任务)
│   ├── M5-bid-generation/     → 标书生成 (12任务)
│   ├── M6-credits-system/     → 积分系统 (8任务)
│   ├── M7-frontend/           → 前端开发 (14任务)
│   └── M8-testing/            → 测试部署 (10任务)
│
├── 📏 coding-standards.md     # 代码规范
├── 🌐 i18n-guide.md           # 多语言开发指南
├── 📚 learning-plan.md        # 技术学习计划
└── 🔄 development-workflow.md # AI协作开发工作流 ⭐新
```

---

## 👤 按角色阅读路径

### 🎓 学习者路径 (理解项目全貌)

**第一步：了解做什么**
1. 阅读本文档的 [项目概述](#-项目概述) 了解业务背景
2. 阅读 [里程碑计划](#-里程碑计划) 了解开发节奏

**第二步：理解怎么做**
1. [system-overview.md](./architecture/system-overview.md) - 理解技术架构
2. [data-model.md](./architecture/data-model.md) - 理解数据设计
3. [agent-workflow.md](./architecture/agent-workflow.md) - 理解AI核心逻辑

**第三步：学习需要的技术**
1. [learning-plan.md](./learning-plan.md) - 2周技术学习计划(视频为主)

**第四步：了解开发规范**
1. [coding-standards.md](./coding-standards.md) - 代码风格、Git流程

**第五步：掌握 AI 协作开发** ⭐推荐
1. [development-workflow.md](./development-workflow.md) - Opus 4.5 + Mini-Agent 完整开发流程

### ⚡ 快速了解路径 (10分钟速览)

| 想了解 | 阅读 |
|--------|------|
| 项目是做什么的 | 本文档 [项目概述](#-项目概述) |
| 用了什么技术 | 本文档 [技术栈](#技术栈) 或 [system-overview.md](./architecture/system-overview.md) |
| 数据库有哪些表 | [data-model.md](./architecture/data-model.md) 的表格部分 |
| 有哪些API | [openapi.yaml](./api-contracts/openapi.yaml) |
| 开发进度安排 | 本文档 [里程碑计划](#-里程碑计划) |
| 具体开发任务 | `task-specs/M{0-8}-*/README.md` |
| **AI协作开发流程** | [development-workflow.md](./development-workflow.md) ⭐ |

---

## 🤖 Mini-Agent 使用指南

<!-- agent-instructions-start -->

### Agent专用：文档解析规则

本项目文档专为 AI Agent 协作开发设计，以下是解析和使用规则：

#### 1️⃣ 任务规格书结构 (task-specs/M*/)

每个任务遵循固定格式：

```markdown
### M{X}-{NN}: {任务名称} ({执行者})
**优先级**: P{0-2}  
**预估时间**: {N}小时  
**执行者**: Mini-Agent | Opus 4.5

#### 描述
{任务描述}

#### 代码实现
~~~{language}
{参考代码}
~~~

#### 验收标准
- [ ] {标准1}
- [ ] {标准2}

#### 依赖
- M{X}-{NN}, M{Y}-{MM}
```

**解析规则:**
- `执行者: Mini-Agent` = 你需要执行的任务
- `执行者: Opus 4.5` = 架构决策任务，已完成设计，参考实现
- `优先级 P0` = 必须完成，阻塞其他任务
- `优先级 P1` = 重要但不阻塞
- `优先级 P2` = 可延后
- `依赖` = 必须先完成的前置任务

#### 2️⃣ 执行任务的标准流程

```
1. 读取任务规格书 → 理解任务目标
2. 检查依赖 → 确认前置任务已完成
3. 阅读相关架构文档 → 理解上下文
4. 参考代码实现 → 不要完全复制，需适配实际情况
5. 验收标准 → 逐项检查完成情况
6. 提交代码 → 遵循 coding-standards.md 规范
```

#### 3️⃣ 关键文档引用

| 需要 | 查阅 |
|------|------|
| 数据库表结构 | `architecture/data-model.md` |
| API端点定义 | `api-contracts/openapi.yaml` |
| Agent状态定义 | `architecture/agent-workflow.md` |
| 代码风格 | `coding-standards.md` |
| 多语言文本 | `i18n-guide.md` |

#### 4️⃣ 代码位置约定

```
backend/
├── app/
│   ├── api/v1/          # API路由 → 对应 openapi.yaml
│   ├── models/          # SQLAlchemy模型 → 对应 data-model.md
│   ├── schemas/         # Pydantic模型 → 对应 openapi.yaml
│   ├── services/        # 业务逻辑
│   ├── agents/          # LangChain/LangGraph → 对应 agent-workflow.md
│   └── core/            # 配置、安全、工具

frontend/
├── src/
│   ├── app/[locale]/    # 页面 → 对应 M7任务
│   ├── components/      # 组件
│   ├── hooks/           # 自定义Hooks
│   ├── services/        # API调用
│   └── i18n/messages/   # 翻译文件 → 对应 i18n-guide.md
```

#### 5️⃣ 任务查找命令

```bash
# 查找所有 Mini-Agent 任务
grep -r "执行者.*Mini-Agent" docs/task-specs/

# 查找所有 P0 优先级任务
grep -r "优先级.*P0" docs/task-specs/

# 查找特定里程碑任务
cat docs/task-specs/M3-llm-service/README.md
```

#### 6️⃣ 常见任务模式

**模式A: CRUD API开发**
```
1. 查看 openapi.yaml 获取端点定义
2. 查看 data-model.md 获取表结构
3. 创建 schemas/{entity}.py
4. 创建 services/{entity}_service.py
5. 创建 api/v1/{entity}.py
6. 编写测试
```

**模式B: 前端页面开发**
```
1. 查看任务规格书中的组件设计
2. 查看 i18n-guide.md 添加翻译键
3. 创建页面 app/[locale]/{path}/page.tsx
4. 创建组件 components/{module}/
5. 使用 shadcn/ui 组件
```

**模式C: Agent节点开发**
```
1. 查看 agent-workflow.md 理解状态定义
2. 查看任务规格书中的节点实现
3. 创建节点 agents/workflows/{workflow}/nodes/
4. 更新工作流图 agents/workflows/{workflow}/graph.py
5. 添加Prompt模板 agents/prompts/templates/
```

<!-- agent-instructions-end -->

> 📚 **更详细的 AI 协作开发指南**: 如需了解完整的 Opus 4.5 + Mini-Agent 协作开发流程，
> 包括具体的 Prompt 模板、完整示例和常见问题排查，请阅读 
> [development-workflow.md](./development-workflow.md)

---

## 📊 项目速览表

| 维度 | 内容 |
|------|------|
| **项目名称** | BidAgent - 多边机构投标AI Agent |
| **核心功能** | 招标机会爬取 → TOR分析 → 标书生成 |
| **目标用户** | 咨询公司、个人顾问 |
| **技术栈** | Next.js 15 + FastAPI + PostgreSQL + LangGraph + DeepSeek |
| **商业模式** | 预付费积分，平台提供LLM API |
| **MVP范围** | 仅ADB，中英文 |
| **开发周期** | 12周 |
| **任务总数** | 80个 (Opus 15 + Mini-Agent 65) |

### 核心数据表 (9张)

| 表名 | 用途 |
|------|------|
| `users` | 用户账户 |
| `bid_opportunities` | 投标机会 |
| `projects` | 用户项目 |
| `documents` | 项目文档 |
| `document_embeddings` | 向量索引 |
| `generated_documents` | 生成的标书 |
| `credit_transactions` | 积分流水 |
| `llm_usages` | LLM调用记录 |
| `recharge_orders` | 充值订单 |

### 核心API模块 (7组)

| 模块 | 端点前缀 |
|------|----------|
| 认证 | `/api/v1/auth/*` |
| 用户 | `/api/v1/users/*` |
| 机会 | `/api/v1/opportunities/*` |
| 项目 | `/api/v1/projects/*` |
| 文档 | `/api/v1/documents/*` |
| 生成 | `/api/v1/projects/{id}/generate/*` |
| 积分 | `/api/v1/credits/*` |

---

## 📋 项目概述

**BidAgent** 是一个面向咨询公司和个人顾问的智能投标助手平台，通过AI Agent自动化完成：

- 🔍 **机会发现**: 自动爬取ADB/WB/UN招标公告
- 📄 **文档分析**: 智能解析TOR/RFP文档，提取关键要求
- ✍️ **标书生成**: AI辅助生成技术方案、公司资质、专家简历等
- 📊 **投标管理**: 跟踪投标进度，管理历史项目

### 商业模式
- **预付费积分包**: 用户购买积分，按使用量扣费
- **平台统一提供LLM API**: 基于DeepSeek，用户无需自备API Key

### 技术栈
| 层级 | 技术选型 |
|------|---------|
| 前端 | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui |
| 后端 | FastAPI, Python 3.11+, LangChain, LangGraph |
| 数据库 | PostgreSQL 16, pgvector, Redis |
| LLM | DeepSeek-V3 (主), DeepSeek-R1 (复杂推理) |
| 基础设施 | Docker, Nginx, Cloudflare |

### MVP范围
- **Phase 1**: 仅支持 ADB (亚洲开发银行)
- **语言**: 中文、英文 (法语后期)

---

## 📚 文档目录

### 1. 架构设计
| 文档 | 描述 |
|------|------|
| [系统架构](./architecture/system-overview.md) | 整体架构、技术选型、部署方案 |
| [数据模型](./architecture/data-model.md) | 数据库Schema、实体关系、索引策略 |
| [Agent工作流](./architecture/agent-workflow.md) | LangGraph工作流、状态机设计 |

### 2. API契约
| 文档 | 描述 |
|------|------|
| [OpenAPI规范](./api-contracts/openapi.yaml) | REST API完整定义 |

### 3. 任务规格书 (Task Specs)
按里程碑组织的详细开发任务，包含Opus 4.5核心任务和Mini-Agent执行任务。

| 里程碑 | 描述 | 任务数 |
|--------|------|--------|
| [M0-基础设施](./task-specs/M0-infrastructure/) | 项目初始化、CI/CD、Docker | 8 |
| [M1-用户系统](./task-specs/M1-user-system/) | 认证、权限、用户管理 | 10 |
| [M2-爬虫模块](./task-specs/M2-crawler/) | ADB网站爬取、数据清洗 | 8 |
| [M3-LLM服务](./task-specs/M3-llm-service/) | DeepSeek集成、积分扣费 | 10 |
| [M4-文档处理](./task-specs/M4-document-processing/) | PDF解析、向量存储 | 10 |
| [M5-标书生成](./task-specs/M5-bid-generation/) | Agent工作流、模板管理 | 12 |
| [M6-积分系统](./task-specs/M6-credits-system/) | 充值、消费、账单 | 8 |
| [M7-前端页面](./task-specs/M7-frontend/) | UI组件、页面开发 | 10 |
| [M8-测试部署](./task-specs/M8-testing/) | 测试、部署、监控 | 4 |

### 4. 开发规范
| 文档 | 描述 |
|------|------|
| [代码规范](./coding-standards.md) | 命名、目录、Git、代码审查 |
| [多语言指南](./i18n-guide.md) | i18n实现、翻译流程 |
| [学习计划](./learning-plan.md) | 4周技术学习路线 |

---

## 🚀 快速开始

### 环境要求
```bash
# WSL2/Ubuntu 环境
Ubuntu >= 22.04 (WSL2)
Node.js >= 20.x
Python >= 3.11
PostgreSQL >= 16
Redis >= 7.0
Docker Desktop (启用 WSL2 集成)
```

### 本地开发
```bash
# 克隆项目到 WSL 文件系统 (推荐，I/O 性能更好)
cd ~
mkdir -p projects && cd projects
git clone <repo-url>
cd bid_agent

# 启动数据库服务
docker compose up -d postgres redis

# 后端
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端 (新终端)
cd frontend
npm install
npm run dev
```

> 📖 **完整环境搭建指南**: 请参阅 [WSL 环境搭建指南](./wsl-setup-guide.md)

---

## 👥 开发团队分工

### Opus 4.5 (架构师角色) - 15个核心任务
- 系统架构设计
- 数据模型设计  
- Agent工作流设计
- Prompt Engineering
- 代码审查
- 技术难点攻关

### Mini-Agent (执行角色) - 65个任务
- CRUD接口开发
- 前端页面实现
- 单元测试编写
- 文档补充

---

## 📅 里程碑计划

| 里程碑 | 周期 | 目标 |
|--------|------|------|
| M0 基础设施 | Week 1 | 项目骨架搭建完成 |
| M1 用户系统 | Week 2 | 注册登录、权限可用 |
| M2 爬虫模块 | Week 3 | ADB数据自动入库 |
| M3 LLM服务 | Week 4 | DeepSeek调用稳定 |
| M4 文档处理 | Week 5-6 | PDF解析、向量检索 |
| M5 标书生成 | Week 7-8 | Agent生成初版标书 |
| M6 积分系统 | Week 9 | 充值消费闭环 |
| M7 前端完善 | Week 10-11 | UI/UX优化 |
| M8 测试上线 | Week 12 | MVP发布 |

---

## 📝 更新日志

### 2026-01-14
- 迁移开发环境至 WSL2/Ubuntu
- 新增 [WSL 环境搭建指南](./wsl-setup-guide.md)
- Windows 开发文档存档至 `docs/archive/windows-legacy/`

### 2026-01-13
- 初始化文档结构
- 完成架构设计文档
- 定义API契约
- 定义API契约

---

## 📞 联系方式

如有问题，请联系项目负责人。
