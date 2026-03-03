# BidAgent V2 Copilot Instructions

## 项目概述

BidAgent V2 是多边机构投标 AI Agent Web 平台，支持 ADB/WB/AfDB 投标。核心流程：**招标获取 (API/RSS) → TOR/RFP 分析 → AI 指导标书编制**

**状态**: V2 重构中 — 开发文档完成，代码从零搭建。

**核心理念**: AI 不直接生成标书文档，而是通过问答式交互指导用户按招标文件要求自行编写。

**技术栈**: Next.js 15 + FastAPI + PostgreSQL 16 (pgvector) + Redis + LangGraph + DeepSeek

## 开发文档 (必读)

所有设计文档在 `docs/v2/`，写代码前请先阅读：

| 文档 | 内容 |
|------|------|
| `docs/v2/01-prd.md` | 产品需求、用户流程、功能优先级 |
| `docs/v2/02-architecture.md` | 系统架构、三层 Agent (MCP + Skills + LangGraph) |
| `docs/v2/03-data-model.md` | 34 表设计、枚举、向量索引、ER 图 |
| `docs/v2/04-openapi.md` | 97 个 API 端点及请求/响应 schema |
| `docs/v2/05-agent-workflow.md` | LLM Client、Skills、LangGraph 工作流、RAG、Prompt |
| `docs/v2/06-frontend-design.md` | 路由、组件、Zustand、TanStack Query、SSE |
| `docs/v2/07-dev-standards.md` | 代码风格、Git 工作流、测试、环境配置 |

## 架构分层

```
backend/app/
├── api/v1/           # REST 路由
├── models/           # SQLAlchemy ORM (继承 Base)
├── schemas/          # Pydantic 请求/响应
├── services/         # 业务逻辑 (注入 AsyncSession)
├── agents/           # LangGraph + Skills + MCP + Prompts
│   ├── llm_client.py # DeepSeek API 封装
│   ├── skills/       # 分析能力单元
│   ├── workflows/    # LangGraph 工作流
│   ├── mcp/          # MCP Tools
│   └── prompts/      # Prompt 模板
├── fetchers/         # API/RSS 招标获取器 (继承 BaseFetcher)
├── tasks/            # Celery 异步任务
└── core/             # 安全、异常、配置

frontend/src/
├── app/[locale]/     # App Router 页面 (zh/en)
├── components/       # shadcn/ui 组件
├── stores/           # Zustand 状态管理
├── services/         # API 客户端 (axios)
├── hooks/            # TanStack Query hooks
└── i18n/messages/    # 翻译 JSON
```

## 关键模式

### Service 层
```python
class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
```

### 三层 Agent 架构
```
MCP Tools (数据检索) → Skills (分析单元) → LangGraph Workflows (编排)
```

### 异常处理
```python
raise NotFoundError(resource_type="User", resource_id=user_id)
raise InsufficientCreditsError(required=100, available=50)
```

## 代码规范

| 后端 (Python) | 前端 (TypeScript) |
|---------------|-------------------|
| Ruff 格式化，行长 88 | Prettier, tabWidth 2 |
| **必须**有类型提示 | 禁止 `any` |
| `snake_case` 函数 | `camelCase` 函数 |
| `datetime.now(UTC)` | `next-intl` 国际化 |
| UUID v4 主键 | Zustand + TanStack Query |

## LLM 集成

- **调用入口**: `agents/llm_client.py` (AsyncOpenAI, DeepSeek 兼容)
- **模型**: DeepSeek-V3 (通用) / DeepSeek-R1 (推理)
- **Embedding**: 腾讯混元 (主, 1024 维) + 智谱 (降级)
- **积分**: `X-Credits-Consumed` / `X-Credits-Remaining`

## Git 提交格式

`<type>(<scope>): <description>` — 例如 `feat(fetcher): 添加AfDB RSS获取器`
