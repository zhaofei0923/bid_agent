# BidAgent Copilot Instructions

## 项目概述

BidAgent 是一个多边机构投标 AI Agent Web 平台，帮助用户完成 ADB/WB/UN 等机构的投标工作。核心流程：**招标机会爬取 → TOR/RFP 文档分析 → AI 标书生成**。

**技术栈**: Next.js 15 + FastAPI + PostgreSQL 16 (pgvector) + Redis + LangGraph + DeepSeek

## 开发模式：文档驱动开发

本项目采用 **文档驱动开发 (Doc-Driven Development)** 模式：

```
任务文档 (task-specs) → Mini-Agent 读取执行 → 代码产出 → Opus 4.5 审查
```

### AI 角色分工

| AI 工具 | 角色 | 使用场景 |
|---------|------|---------|
| **Opus 4.5** (Copilot Chat) | 架构师/文档作者 | 编写任务文档、架构设计、代码审查、疑难诊断 |
| **Mini-Agent** (CLI) | 主执行者 | 读取 task-specs 自动执行开发任务 |
| **Claude Code** (独立客户端) | 补充编码 | 交互式修改、实时调试、细节补充 |

### Opus 4.5 核心职责

作为 Copilot Chat 中的 Opus 4.5，你的主要职责是：

1. **编写任务规格文档** - 按 `docs/task-spec-template.md` 格式生成 Mini-Agent 可执行的任务文档
2. **架构设计** - 设计新模块架构、数据模型、API 接口
3. **代码审查** - 审查 Mini-Agent 生成的代码，检查安全性、性能、规范符合性
4. **疑难诊断** - 分析复杂 bug、提供技术方案

### 任务文档格式要点

当需要编写任务文档时，使用以下结构：

```yaml
---
id: M1-03                    # 任务ID: M{里程碑}-{序号}
title: 任务标题
executor: mini-agent         # mini-agent | opus
priority: P0                 # P0(阻塞) | P1(重要) | P2(一般)
task_type: coding            # coding | testing | documentation | design | research
dependencies: [M1-01, M1-02] # 依赖任务
outputs:                     # 输出文件列表
  - backend/app/xxx.py
acceptance_criteria:         # 验收标准
  - 标准1
  - 标准2
---

## 描述 / 输入 / 输出文件 / 验收标准 / 详细步骤 / 代码模板
```

## 架构与代码位置

```
backend/app/
├── api/v1/           # REST 路由 → 对应 docs/api-contracts/openapi.yaml
├── models/           # SQLAlchemy 模型 → 对应 docs/architecture/data-model.md
├── schemas/          # Pydantic 请求/响应模型
├── services/         # 业务逻辑层
├── agents/           # LangGraph 工作流 → 对应 docs/architecture/agent-workflow.md
│   ├── workflows/    # 状态机定义 (Intake → Analysis → Planning → Generation)
│   └── prompts/      # Prompt 模板
└── core/             # 安全、配置、工具

frontend/src/
├── app/[locale]/     # Next.js App Router 页面 (支持 zh/en)
├── components/       # React 组件 (使用 shadcn/ui)
├── hooks/            # 自定义 Hooks
├── services/         # API 调用层
└── i18n/messages/    # 翻译文件 (zh.json, en.json)
```

## 关键开发模式

### CRUD API 开发流程
1. 查看 `docs/api-contracts/openapi.yaml` 获取端点定义
2. 查看 `docs/architecture/data-model.md` 获取表结构
3. 创建 `schemas/{entity}.py` (Pydantic)
4. 创建 `services/{entity}_service.py` (业务逻辑)
5. 创建 `api/v1/{entity}.py` (路由)

### Agent 节点开发流程
1. 理解 `docs/architecture/agent-workflow.md` 中的状态定义
2. 节点放在 `agents/workflows/{workflow}/nodes/`
3. 更新 `agents/workflows/{workflow}/graph.py`
4. Prompt 模板放在 `agents/prompts/templates/`

### 前端页面开发
1. 页面放在 `app/[locale]/{path}/page.tsx`
2. 组件使用 shadcn/ui，放在 `components/{module}/`
3. 所有 UI 文本必须通过 `next-intl` 国际化，键定义在 `i18n/messages/`

## 代码规范

### Python (后端)
- 使用 **Ruff** 格式化，行长 88
- **必须**有类型提示：`async def get_user(db: AsyncSession, email: str) -> User | None:`
- 异步：使用 `asyncio.gather()` 并行处理，避免阻塞 IO (`aiofiles` 代替 `open`)
- 异常：继承 `BidAgentException`，包含 `code` 和 `message` 字段
- 命名：`snake_case` (函数/变量)，`PascalCase` (类)

### TypeScript (前端)
- 文件名：小写短横线 (`use-auth.ts`, `project-card.tsx`)
- 函数名：`camelCase`；常量：`UPPER_SNAKE_CASE`
- 组件：使用函数组件 + `memo()`，Props 接口明确定义
- 禁止 `any`，使用 `unknown` 或具体类型

### Git 提交
- 格式：`<type>(<scope>): <description>` 例如 `feat(auth): 添加JWT刷新`
- type: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

## LLM 集成要点

- **主模型**: DeepSeek-V3 (通用任务)，DeepSeek-R1 (复杂推理)
- 所有 LLM 调用通过 `agents/llm_client.py` 统一封装
- 调用需要扣积分：响应头含 `X-Credits-Consumed`, `X-Credits-Remaining`
- 积分不足抛出 `InsufficientCreditsError(required, available)`

## 开发环境

```bash
# 开发环境: 原生 Ubuntu 系统
# 环境搭建: docs/development-environment.md

# 启动服务
docker compose up -d postgres redis
cd backend && uvicorn app.main:app --reload  # :8000
cd frontend && npm run dev                    # :3000

# Mini-Agent 执行任务
mini-agent run docs/task-specs/M1-user-system/README.md --task M1-03
```

## 核心文档参考

| 需求 | 文档路径 |
|------|---------|
| 开发环境搭建 | `docs/development-environment.md` |
| 开发工作流 | `docs/development-workflow.md` |
| AI 协作指南 | `docs/ai-collaboration-guide.md` |
| 任务文档模板 | `docs/task-spec-template.md` |
| API 定义 | `docs/api-contracts/openapi.yaml` |
| 数据库表 | `docs/architecture/data-model.md` |
| Agent 状态机 | `docs/architecture/agent-workflow.md` |
| 国际化 | `docs/i18n-guide.md` |
| 任务规格 | `docs/task-specs/M{0-8}-*/README.md` |
