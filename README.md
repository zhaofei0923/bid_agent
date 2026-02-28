# BidAgent V2 — 多边机构投标 AI Agent 平台

> **状态: V2 重构中** — 本仓库已清理 V1 代码，仅保留 V2 开发文档作为重建蓝图。

## 项目概述

BidAgent 是 AI 驱动的多边发展银行投标辅助平台，帮助咨询公司自动化处理 ADB/WB/UN 招标全流程。

**核心工作流**: 招标爬取 → TOR/RFP 分析 → AI 指导标书编制 → 质量审查

**技术栈**: Next.js 15 + FastAPI + PostgreSQL 16 (pgvector) + Redis + LangGraph + DeepSeek

## V2 开发文档

| # | 文档 | 内容 |
|---|------|------|
| 1 | [产品需求文档](docs/v2/01-prd.md) | 用户角色、功能模块、P0/P1/P2 优先级 |
| 2 | [技术架构设计](docs/v2/02-architecture.md) | 三层 Agent 架构、MCP + Skills + LangGraph |
| 3 | [数据模型设计](docs/v2/03-data-model.md) | 34 表完整 schema、ER 图、向量索引 |
| 4 | [API 契约文档](docs/v2/04-openapi.md) | 97 个端点、请求/响应 schema |
| 5 | [Agent 工作流设计](docs/v2/05-agent-workflow.md) | LLM Client、Skills、LangGraph 8 节点工作流、RAG、Prompt 模板 |
| 6 | [前端设计文档](docs/v2/06-frontend-design.md) | 路由、组件、Zustand、TanStack Query、SSE |
| 7 | [开发规范](docs/v2/07-dev-standards.md) | 代码风格、Git 工作流、测试策略、环境配置 |

## 快速开始 (V2 重建后)

```bash
# 1. 基础设施
docker compose up -d postgres redis

# 2. 后端
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# 3. 前端
cd frontend && npm install && npm run dev
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 15 + TypeScript + Tailwind CSS + shadcn/ui + Zustand + TanStack Query |
| 后端 | FastAPI + SQLAlchemy 2.0 (async) + Pydantic v2 + Celery |
| AI | DeepSeek (V3 + R1) + LangGraph + MCP Tools + Skills |
| 数据 | PostgreSQL 16 + pgvector (1024-dim) + Redis 7 |
| 向量 | 腾讯混元 Embedding (主) + 智谱 (降级) |

## License

MIT

