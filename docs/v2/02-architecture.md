# BidAgent V2 — 技术架构设计

> 版本: 2.0.0 | 日期: 2026-02-11 | 状态: Draft

## 1. 架构全景

### 1.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Client Layer                                  │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Next.js 15 (App Router)  +  shadcn/ui  +  TanStack Query       │   │
│  │  ├── 国际化 (next-intl, zh/en)                                   │   │
│  │  ├── API 客户端 (axios)                                          │   │
│  │  └── 状态管理 (Zustand)                                          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │ HTTPS / REST API
┌──────────────────────────────────┴──────────────────────────────────────┐
│                           API Gateway Layer                             │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  FastAPI (async)                                                  │   │
│  │  ├── JWT 认证 (HS256)                                            │   │
│  │  ├── 速率限制 (Redis 滑动窗口)                                    │   │
│  │  ├── CORS 中间件                                                  │   │
│  │  └── 请求日志中间件                                               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
┌──────────────────────────────────┴──────────────────────────────────────┐
│                           Service Layer                                 │
│  ┌───────────────┐  ┌───────────────┐  ┌────────────────────────────┐  │
│  │  业务服务       │  │  Agent 引擎    │  │  MCP Server                │  │
│  │  ├─ User       │  │  ├─ LangGraph  │  │  ├─ knowledge-search      │  │
│  │  ├─ Project    │  │  │  Workflows  │  │  ├─ bid-document-search   │  │
│  │  ├─ Opportunity│  │  ├─ Skills     │  │  ├─ opportunity-query     │  │
│  │  ├─ Document   │  │  │  Registry   │  │  └─ web-search (future)  │  │
│  │  ├─ Analysis   │  │  └─ LLM Client │  └────────────────────────────┘  │
│  │  ├─ Knowledge  │  │    (DeepSeek)  │                                  │
│  │  ├─ Payment    │  └───────────────┘                                  │
│  │  └─ Stats      │                                                     │
│  └───────────────┘                                                      │
└──────────┬─────────────────┬─────────────────┬──────────────────────────┘
           │                 │                 │
┌──────────┴──────┐ ┌───────┴───────┐ ┌───────┴───────────────────────────┐
│  PostgreSQL 16  │ │    Redis      │ │  Celery Workers                   │
│  + pgvector     │ │  ├─ 缓存      │ │  ├─ 文档处理 (解析/OCR/向量化)    │
│  ├─ 业务表      │ │  ├─ Session   │ │  ├─ 爬虫任务 (ADB/WB/UNGM)       │
│  ├─ 向量索引    │ │  ├─ 速率限制  │ │  └─ 定时任务 (过期关闭)           │
│  └─ 全文搜索    │ │  └─ 工作流状态│ └─────────────────────────────────────┘
└─────────────────┘ └───────────────┘
```

### 1.2 技术选型

| 层级 | 技术 | 版本 | 选型理由 |
|------|------|------|---------|
| **前端框架** | Next.js | 15.x | App Router + Server Components + 内置 SSR/SSG |
| **UI 组件库** | shadcn/ui | latest | Radix UI 基础 + Tailwind CSS，可定制性强 |
| **状态管理** | Zustand | 5.x | 轻量、TypeScript 友好、无 Provider 嵌套 |
| **数据获取** | TanStack Query | 5.x | 缓存/重试/乐观更新，SSR 支持 |
| **HTTP 客户端** | axios | 1.x | 拦截器、请求取消、TypeScript 类型安全 |
| **国际化** | next-intl | 4.x | App Router 原生支持、消息编译 |
| **后端框架** | FastAPI | 0.115+ | 异步、自动 OpenAPI 文档、Pydantic v2 校验 |
| **ORM** | SQLAlchemy | 2.0 | 异步支持 (asyncpg)、成熟的关系映射 |
| **数据库** | PostgreSQL | 16 | pgvector 向量搜索 + JSONB + 全文搜索 |
| **向量扩展** | pgvector | 0.8+ | 余弦距离索引、HNSW |
| **缓存/队列** | Redis | 7.x | Celery Broker + 会话缓存 + 速率限制 |
| **任务队列** | Celery | 5.x | 分布式任务、定时调度、重试机制 |
| **LLM** | DeepSeek | V4 Pro | OpenAI 兼容 API、性价比高 |
| **Embedding** | 腾讯混元 / 智谱 | - | 1024 维、中文优化、多 Provider 降级 |
| **Agent 框架** | LangGraph | 1.x | 状态图工作流、检查点、human-in-the-loop |
| **MCP** | Model Context Protocol | - | 标准化 Agent Tool 调用协议 |
| **OCR** | PaddleOCR | 2.x | 中英文、CPU 运行、免费 |
| **迁移工具** | Alembic | 1.x | SQLAlchemy 配套、版本化迁移 |
| **代码质量** | Ruff / Prettier / ESLint | - | Python Linter + TS Formatter |
| **测试** | pytest / Playwright | - | 后端单元+集成 / 前端 E2E |
| **容器化** | Docker Compose | - | 开发环境一键启动 |

---

## 2. 后端架构

### 2.1 目录结构

```
backend/
├── alembic/                    # 数据库迁移
│   ├── alembic.ini
│   ├── env.py
│   └── versions/               # 迁移版本文件
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口 + lifespan
│   ├── config.py               # Pydantic Settings 配置
│   ├── database.py             # 引擎 + 会话工厂 + get_db
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py     # 路由注册
│   │       ├── auth.py
│   │       ├── projects.py
│   │       ├── opportunities.py
│   │       ├── bid_documents.py
│   │       ├── bid_analysis.py
│   │       ├── bid_plan.py
│   │       ├── bid_prediction.py
│   │       ├── quality_review.py
│   │       ├── guidance.py
│   │       ├── knowledge_base.py
│   │       ├── payment.py
│   │       └── stats.py
│   ├── core/
│   │   ├── exceptions.py       # BidAgentException 层次
│   │   ├── security.py         # JWT + 密码 + 依赖注入
│   │   └── middleware.py       # 速率限制 + 请求日志
│   ├── models/                 # SQLAlchemy ORM 模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── opportunity.py      # 统一的单一模型
│   │   ├── bid_document.py
│   │   ├── bid_analysis.py
│   │   ├── bid_plan.py
│   │   ├── bid_prediction.py
│   │   ├── knowledge_base.py
│   │   ├── expert.py
│   │   ├── payment.py
│   │   └── stats.py
│   ├── schemas/                # Pydantic 请求/响应 Schema
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── opportunity.py
│   │   ├── bid_document.py
│   │   ├── guidance.py
│   │   └── knowledge_base.py
│   ├── services/               # 业务逻辑层
│   │   ├── user_service.py
│   │   ├── project_service.py
│   │   ├── opportunity_service.py
│   │   ├── bid_document_service.py
│   │   ├── bid_analysis_service.py
│   │   ├── bid_plan_service.py
│   │   ├── bid_prediction_service.py
│   │   ├── quality_review_service.py
│   │   ├── knowledge_base_service.py
│   │   ├── translation_service.py
│   │   ├── payment_service.py
│   │   ├── stats_service.py
│   │   ├── document_processing/
│   │   │   ├── pdf_parser.py
│   │   │   ├── docx_parser.py
│   │   │   ├── bid_document_parser.py
│   │   │   └── chunker.py
│   │   └── embedding/
│   │       ├── base.py
│   │       ├── hunyuan.py
│   │       ├── zhipu.py
│   │       └── resilient_client.py
│   ├── agents/
│   │   ├── llm_client.py       # DeepSeek API 封装
│   │   ├── mcp/                # MCP Server 实现
│   │   │   ├── server.py       # MCP Server 注册
│   │   │   └── tools/
│   │   │       ├── knowledge_search.py
│   │   │       ├── bid_document_search.py
│   │   │       └── opportunity_query.py
│   │   ├── skills/             # Skills 注册和实现
│   │   │   ├── registry.py
│   │   │   ├── analyze_qualification.py
│   │   │   ├── evaluate_criteria.py
│   │   │   ├── section_guidance.py
│   │   │   ├── review_draft.py
│   │   │   └── quality_review.py
│   │   ├── prompts/            # Prompt 模板
│   │   │   ├── adb_analysis.py
│   │   │   ├── wb_analysis.py
│   │   │   └── templates/      # Jinja2 模板（可选）
│   │   └── workflows/
│   │       └── bid_guidance/
│   │           ├── graph.py
│   │           ├── state.py
│   │           └── nodes.py
│   ├── crawlers/
│   │   ├── base.py             # 统一 BaseCrawler
│   │   ├── adb.py
│   │   ├── wb.py
│   │   ├── ungm.py             # 从 services/crawlers/ 移入
│   │   └── cloudflare_bypass.py
│   └── tasks/
│       ├── celery.py           # Celery 配置
│       ├── crawler_tasks.py
│       └── document_tasks.py
├── tests/
│   ├── conftest.py
│   ├── api/
│   ├── services/
│   ├── agents/
│   └── crawlers/
├── requirements.txt
├── Dockerfile
└── pytest.ini
```

### 2.2 Service 层模式

所有业务逻辑封装在 Service 类中，通过构造函数注入 `AsyncSession`：

```python
class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: UUID, data: ProjectCreate) -> Project:
        ...

# 路由注入
@router.post("/")
async def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    return await service.create(current_user.id, data)
```

### 2.3 异常处理

```python
class BidAgentException(Exception):
    code: str
    message: str
    status_code: int = 500

class NotFoundError(BidAgentException):        # 404
class UnauthorizedError(BidAgentException):     # 401
class ForbiddenError(BidAgentException):        # 403
class ValidationError(BidAgentException):       # 422
class InsufficientCreditsError(BidAgentException):  # 402
class ExternalServiceError(BidAgentException):  # 502
```

全局异常处理器将 `BidAgentException` 转为统一 JSON 响应：
```json
{
  "code": "NOT_FOUND",
  "message": "Project not found",
  "detail": null
}
```

### 2.4 启动生命周期

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    validate_config()       # 检查 API Key 配置
    await validate_database()  # 检查 pgvector + 向量维度
    await validate_redis()     # 检查 Redis, 失败则降级
    yield
    # Shutdown
    await engine.dispose()
```

---

## 3. Agent 架构

### 3.1 三层 Agent 架构

```
┌──────────────────────────────────────────────┐
│              LangGraph Workflows             │  ← 编排层: 多步骤工作流
│  ┌────────────┐  ┌─────────────────────┐     │
│  │ 标书指导流  │  │ 招标分析流 (新增)    │     │
│  └──────┬─────┘  └──────────┬──────────┘     │
└─────────┼───────────────────┼────────────────┘
          │                   │
┌─────────┴───────────────────┴────────────────┐
│              Skills Layer                     │  ← 能力层: 封装固定分析流程
│  ┌──────────────┐  ┌──────────────────────┐  │
│  │ analyze_qual │  │ section_guidance      │  │
│  │ eval_criteria│  │ review_draft          │  │
│  └──────┬───────┘  └──────────┬───────────┘  │
└─────────┼──────────────────────┼─────────────┘
          │                      │
┌─────────┴──────────────────────┴─────────────┐
│              MCP Tools Layer                  │  ← 工具层: 数据检索原语
│  ┌────────────────┐  ┌─────────────────────┐ │
│  │ knowledge_search│  │ bid_document_search │ │
│  │ opportunity_qry │  │ web_search (future) │ │
│  └────────────────┘  └─────────────────────┘ │
└──────────────────────────────────────────────┘
          │                      │
    ┌─────┴──────┐         ┌────┴─────┐
    │ pgvector   │         │ DeepSeek │
    │ PostgreSQL │         │ LLM API  │
    └────────────┘         └──────────┘
```

### 3.2 MCP Server 设计

MCP (Model Context Protocol) 将数据检索暴露为标准化工具，Agent 自主决定何时调用。

#### Tool: `knowledge_search`
```json
{
  "name": "knowledge_search",
  "description": "从知识库中搜索 ADB/WB 采购准则和参考文档",
  "parameters": {
    "query": "搜索查询文本",
    "institution": "adb | wb | un (可选，不传则搜所有)",
    "kb_type": "guide | review | template (可选)",
    "top_k": "返回结果数量，默认 5",
    "score_threshold": "相似度阈值，默认 0.5"
  },
  "returns": "List[{content, score, source_document, page_number}]"
}
```

#### Tool: `bid_document_search`
```json
{
  "name": "bid_document_search",
  "description": "从项目招标文件中搜索相关内容分块",
  "parameters": {
    "project_id": "项目 UUID",
    "query": "搜索查询文本",
    "section_types": "限定章节类型列表 (可选)",
    "top_k": "返回数量，默认 5",
    "score_threshold": "阈值，默认 0.3"
  },
  "returns": "List[{content, score, section_type, page_number, clause_reference}]"
}
```

#### Tool: `opportunity_query`
```json
{
  "name": "opportunity_query",
  "description": "查询招标机会数据库",
  "parameters": {
    "opportunity_id": "机会 UUID (精确查询)",
    "search": "关键词搜索 (模糊查询)",
    "source": "adb | wb | un",
    "fields": "返回字段列表"
  },
  "returns": "Opportunity 或 List[Opportunity]"
}
```

### 3.3 Skills 设计

Skills 封装固定的分析流程，内部可调用 MCP Tools + LLM。

```python
class Skill(ABC):
    name: str
    description: str
    
    @abstractmethod
    async def execute(self, context: SkillContext) -> SkillResult:
        """执行 Skill"""
        ...

class SkillContext:
    project_id: str
    db: AsyncSession
    llm_client: LLMClient
    mcp_tools: MCPToolkit    # 可调用 MCP Tools
    parameters: dict         # Skill 特定参数

class SkillResult:
    success: bool
    data: dict               # 结构化输出
    tokens_consumed: int
    sources: List[dict]      # 引用的来源
```

**已定义 Skills**:

| Skill | 功能 | 内部调用 |
|-------|------|---------|
| `AnalyzeQualification` | 资质要求分析 | bid_document_search(qualification) + knowledge_search(ADB资质) + LLM |
| `EvaluateCriteria` | 评分标准提取 | bid_document_search(evaluation) + knowledge_search(评标方法) + LLM |
| `SectionGuidance` | 章节编写指导 | bid_document_search(相关章节) + knowledge_search(模板) + LLM |
| `ReviewDraft` | 用户草稿审查 | bid_document_search(要求) + LLM (4 维度) |
| `QualityReview` | 全文质量审查 | bid_document_search(全文) + LLM (4 维度) |
| `ExtractDates` | 关键日期提取 | bid_document_search(dates) + LLM |
| `AnalyzeRisk` | 风险评估 | 综合其他 Skill 结果 + LLM |

### 3.4 LLM 客户端

```python
class LLMClient:
    """DeepSeek API 封装 (OpenAI 兼容格式)"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,  # https://api.deepseek.com
        )
        self.model = settings.LLM_MODEL      # deepseek-v4-pro
    
    async def chat(
        self, messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> LLMResponse: ...
    
    async def chat_stream(
        self, messages: List[Message],
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]: ...
    
    async def generate_with_context(
        self, query: str, context: str,
        system_prompt: str = "",
        temperature: float = 0.3,
    ) -> LLMResponse: ...
```

### 3.5 Embedding 弹性架构

```
┌─────────────────────────────────────────┐
│         ResilientEmbeddingClient        │
│  ┌─────────────┐  ┌─────────────────┐  │
│  │ 混元 (主)    │──│ 智谱 (降级)     │  │
│  │ 1024 维      │  │ 1024 维         │  │
│  │ batch=16     │  │ batch=64        │  │
│  └─────────────┘  └─────────────────┘  │
│  指数退避重试 (3 次, 1s 基础)           │
│  运行时热切换 Provider                  │
└─────────────────────────────────────────┘
```

接口:
```python
class BaseEmbeddingClient(ABC):
    dimension: int  # 1024
    
    async def embed_text(self, text: str) -> List[float]
    async def embed_texts(self, texts: List[str]) -> List[List[float]]
    async def embed_query(self, query: str) -> List[float]
```

---

## 4. 前端架构

### 4.1 目录结构

```
frontend/
├── src/
│   ├── app/
│   │   └── [locale]/
│   │       ├── layout.tsx          # 根布局 + IntlProvider
│   │       ├── page.tsx            # 首页
│   │       ├── auth/
│   │       │   ├── login/page.tsx
│   │       │   └── register/page.tsx
│   │       ├── dashboard/page.tsx
│   │       ├── opportunities/
│   │       │   ├── page.tsx        # 列表
│   │       │   └── [id]/page.tsx   # 详情
│   │       ├── projects/
│   │       │   ├── page.tsx        # 列表
│   │       │   └── [id]/page.tsx   # 详情
│   │       ├── bid/
│   │       │   └── [projectId]/page.tsx  # 投标工作台
│   │       ├── settings/
│   │       ├── credits/
│   │       └── help/
│   ├── components/
│   │   ├── ui/                    # shadcn/ui 基础组件
│   │   ├── layout/                # Header/Footer/Sidebar
│   │   ├── bid/                   # 投标工作台组件
│   │   ├── opportunities/         # 招标列表组件
│   │   └── common/                # 通用业务组件
│   ├── services/                  # API 客户端层
│   │   ├── api-client.ts          # axios 实例 + 拦截器
│   │   ├── auth.ts
│   │   ├── projects.ts
│   │   ├── opportunities.ts
│   │   ├── bid-documents.ts
│   │   ├── bid-analysis.ts
│   │   ├── knowledge-base.ts
│   │   └── payment.ts
│   ├── hooks/                     # 自定义 Hooks (TanStack Query)
│   │   ├── use-auth.ts
│   │   ├── use-projects.ts
│   │   └── use-bid.ts
│   ├── stores/                    # Zustand 状态
│   │   ├── auth-store.ts
│   │   └── bid-workspace-store.ts
│   ├── lib/                       # 工具函数
│   ├── types/                     # TypeScript 类型
│   └── i18n/
│       ├── config.ts
│       └── messages/
│           ├── zh.json
│           └── en.json
├── public/
├── tests/                         # Playwright E2E
├── next.config.mjs
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

### 4.2 API 客户端层

```typescript
// services/api-client.ts
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL + "/v1",
  timeout: 30000,
});

// 请求拦截器: 注入 JWT
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// 响应拦截器: 401 自动刷新 token
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await refreshToken();
      return apiClient(error.config);
    }
    throw error;
  }
);
```

---

## 5. 数据层架构

### 5.1 数据库连接

```python
# database.py
engine = create_async_engine(
    settings.DATABASE_URL,    # postgresql+asyncpg://...
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
```

### 5.2 向量搜索

使用 pgvector 余弦距离，HNSW 索引:
```sql
-- 创建索引
CREATE INDEX idx_chunks_embedding ON bid_document_chunks
  USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- 搜索查询
SELECT *, 1 - (embedding <=> $1::vector) AS similarity
FROM bid_document_chunks
WHERE project_id = $2
ORDER BY embedding <=> $1::vector
LIMIT $3;
```

### 5.3 迁移管理 (Alembic)

```bash
# 新建迁移
alembic revision --autogenerate -m "add payment tables"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

V2 首次迁移将包含所有表的完整 DDL，不再依赖增量 SQL 文件。

---

## 6. 基础设施

### 6.1 Docker Compose

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]
    environment:
      POSTGRES_DB: bid_agent
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    healthcheck:
      test: pg_isready -U postgres
      interval: 5s

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    healthcheck:
      test: redis-cli ping
      interval: 5s

  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
    env_file: .env

  celery-worker:
    build: ./backend
    command: celery -A app.tasks.celery worker --loglevel=info
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
    env_file: .env

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]
    env_file: .env

volumes:
  pgdata:
```

### 6.2 开发环境启动

```bash
# 1. 启动基础设施
docker compose up -d postgres redis

# 2. 后端
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 3. Celery Worker
celery -A app.tasks.celery worker --loglevel=info

# 4. 前端
cd frontend
npm install
npm run dev
```

---

## 7. 环境变量清单

### 7.1 应用配置

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `APP_ENV` | 否 | development | 环境: development / production |
| `DEBUG` | 否 | true | 调试模式 |
| `SECRET_KEY` | **是** | - | JWT 签名密钥 |
| `API_V1_PREFIX` | 否 | /v1 | API 路由前缀 |
| `CORS_ORIGINS` | 否 | ["http://localhost:3000"] | CORS 允许来源 |

### 7.2 数据库

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `DATABASE_URL` | **是** | postgresql+asyncpg://postgres:postgres@localhost:5432/bid_agent | 异步连接串 |
| `REDIS_URL` | **是** | redis://localhost:6379/0 | Redis 连接 |

### 7.3 LLM

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `LLM_API_KEY` | **是** | - | DeepSeek API Key |
| `LLM_BASE_URL` | 否 | https://api.deepseek.com | OpenAI 兼容端点 |
| `LLM_MODEL` | 否 | deepseek-v4-pro | 通用模型 |
| `LLM_REASONING_MODEL` | 否 | deepseek-v4-pro | 复杂推理模型 |

### 7.4 Embedding

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `EMBEDDING_PROVIDER` | 否 | hunyuan | 主 Provider: hunyuan / zhipu |
| `EMBEDDING_DIMENSION` | 否 | 1024 | 向量维度 |
| `EMBEDDING_FALLBACK_ENABLED` | 否 | true | 启用自动降级 |
| `HUNYUAN_SECRET_ID` | 条件 | - | 腾讯云 SecretId |
| `HUNYUAN_SECRET_KEY` | 条件 | - | 腾讯云 SecretKey |
| `ZHIPU_API_KEY` | 条件 | - | 智谱 API Key |

### 7.5 Celery

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `CELERY_BROKER_URL` | 否 | redis://localhost:6379/1 | Broker |
| `CELERY_RESULT_URL` | 否 | redis://localhost:6379/2 | Result Backend |

### 7.6 爬虫

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `CRAWLER_REQUEST_DELAY` | 否 | 10.0 | 请求间隔(秒) |

### 7.7 前端

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `NEXT_PUBLIC_API_URL` | **是** | http://localhost:8000 | 后端 API 地址 |
| `NEXT_PUBLIC_APP_URL` | 否 | http://localhost:3000 | 前端地址 |

### 7.8 支付（P1，后续配置）

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `ALIPAY_APP_ID` | 条件 | - | 支付宝应用 ID |
| `ALIPAY_PRIVATE_KEY` | 条件 | - | 支付宝私钥 |
| `ALIPAY_PUBLIC_KEY` | 条件 | - | 支付宝公钥 |
| `WECHAT_APP_ID` | 条件 | - | 微信支付应用 ID |
| `WECHAT_MCH_ID` | 条件 | - | 微信商户号 |
| `WECHAT_API_KEY` | 条件 | - | 微信支付密钥 |

### 7.9 翻译（P1）

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `TENCENT_TRANSLATE_SECRET_ID` | 条件 | - | 腾讯云翻译 SecretId |
| `TENCENT_TRANSLATE_SECRET_KEY` | 条件 | - | 腾讯云翻译 SecretKey |

---

## 8. 关键架构决策 (ADR)

### ADR-001: 统一 UUID 主键

**决策**: 所有表统一使用 `UUID(as_uuid=True)` 作为主键
**原因**: V1 中 UUID 与 String(36) 混用导致 FK 类型不匹配、代码风格不一致
**影响**: 所有模型、Schema、前端类型统一为 UUID string

### ADR-002: 单一 Opportunity 模型

**决策**: 合并 `Opportunity` 和 `BidOpportunity` 为单一 `opportunities` 表
**原因**: V1 中两个功能重叠的表导致数据不一致
**方案**: 保留 UUID 主键的版本，添加 `search_vector` (TSVECTOR) 全文搜索列

### ADR-003: 统一爬虫基类

**决策**: 所有爬虫统一继承 `app.crawlers.base.BaseCrawler`
**原因**: V1 中 ADB/WB 和 UNGM 分别在不同目录使用不同基类
**方案**: UNGM 爬虫迁入 `app/crawlers/ungm.py`

### ADR-004: MCP + Skills 混合架构

**决策**: 基础数据检索暴露为 MCP Tools，固定分析流程封装为 Skills
**原因**: MCP 提供标准化 Tool 调用协议，Skills 封装高层业务逻辑
**方案**: Skills 内部可调用 MCP Tools，LangGraph 节点可调用 Skills

### ADR-005: Alembic 替代手工 SQL

**决策**: 使用 Alembic 做版本化数据库迁移
**原因**: V1 的 10 个手工 SQL 文件顺序混乱（两个 004_ 前缀），无回滚支持
**方案**: V2 首个迁移包含完整 DDL，后续用 `--autogenerate`

### ADR-006: Redis 存储工作流状态

**决策**: LangGraph 工作流状态从内存字典迁移到 Redis
**原因**: V1 使用 `_workflow_runs: dict = {}` 内存存储，多 worker 部署状态丢失
**方案**: 使用 `langgraph.checkpoint.redis.RedisSaver`

### ADR-007: datetime.now(UTC) 替代 utcnow()

**决策**: 所有时间戳使用 `datetime.now(timezone.utc)`
**原因**: `datetime.utcnow()` 在 Python 3.12+ 中已弃用
**方案**: 模型 default 使用 `lambda: datetime.now(timezone.utc)`
