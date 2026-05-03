# BidAgent V2 — 开发规范

> 版本: 2.0.0 | 日期: 2026-02-11 | 状态: Draft

## 1. 代码风格

### 1.1 Python (Backend)

| 项目 | 规范 |
|------|------|
| 格式化 | Ruff (line-length: 88) |
| import 排序 | Ruff isort (stdlib → third-party → local) |
| 命名 | `snake_case` 函数/变量, `PascalCase` 类, `UPPER_SNAKE_CASE` 常量 |
| 类型提示 | **必需** — 所有公开 API 函数参数和返回值 |
| 文档字符串 | Google style docstring |
| 异步 | 优先 `asyncio.gather()` 并行; 禁止阻塞 I/O |
| 字符串 | 优先 f-string; 长 SQL 用三引号 |
| 日期 | `datetime.now(UTC)` (禁止 `datetime.utcnow()`) |
| ID | UUID v4 (所有主键统一) |

**Ruff 配置 (`pyproject.toml`)**:
```toml
[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "SIM", "RUF"]
ignore = ["E501"]  # line-length 由 formatter 处理

[tool.ruff.lint.isort]
known-first-party = ["app"]
```

### 1.2 TypeScript (Frontend)

| 项目 | 规范 |
|------|------|
| 格式化 | Prettier (semi: false, singleQuote: false, tabWidth: 2) |
| Lint | ESLint + @next/eslint-plugin-next |
| 文件命名 | `kebab-case.ts(x)` (组件文件 `PascalCase.tsx`) |
| 函数命名 | `camelCase` |
| 组件命名 | `PascalCase` + `memo()` |
| 类型 | **禁止 `any`** — 使用 `unknown` 或显式类型 |
| Props | 每个组件定义 `interface XxxProps` |
| i18n | 所有 UI 文本通过 `next-intl` |
| 导入 | 绝对路径 `@/components/...` |

**ESLint 关键规则**:
```javascript
{
  "rules": {
    "@typescript-eslint/no-explicit-any": "error",
    "react/function-component-definition": ["error", { "namedComponents": "function-declaration" }],
    "import/order": ["error", { "groups": ["builtin", "external", "internal"] }]
  }
}
```

---

## 2. 项目结构规范

### 2.1 目录强制约定

```
backend/app/
├── api/v1/           # 路由: 仅依赖注入 + 调用 service
├── models/           # SQLAlchemy ORM 模型
├── schemas/          # Pydantic 请求/响应 schema
├── services/         # 业务逻辑层 (注入 AsyncSession)
├── agents/           # LangGraph + Skills + Prompts
│   ├── llm_client.py
│   ├── skills/       # Skill 实现
│   ├── workflows/    # LangGraph 工作流
│   ├── mcp/          # MCP Tools
│   └── prompts/      # Prompt 模板
├── crawlers/         # 爬虫 (继承 BaseCrawler)
├── tasks/            # Celery 任务
└── core/             # 安全、异常、配置
```

### 2.2 层级依赖规则

```
api/ → services/ → models/、agents/
     ↗           ↗
schemas/    core/
```

- `api/` 不直接访问 `models/`，通过 `services/` 间接访问
- `services/` 不导入 `api/` — 禁止循环依赖
- `agents/` 可调用 `services/` 获取数据
- `core/` 为基础层，不依赖其他业务层

---

## 3. API 设计规范

### 3.1 路由命名

```
GET    /v1/{resource}                 # 列表 (分页)
POST   /v1/{resource}                 # 创建
GET    /v1/{resource}/{id}            # 详情
PUT    /v1/{resource}/{id}            # 全量更新
PATCH  /v1/{resource}/{id}            # 部分更新
DELETE /v1/{resource}/{id}            # 删除
POST   /v1/{resource}/{id}/{action}   # 操作
```

### 3.2 响应格式

```python
# 成功 - 单个
{"id": "uuid", "name": "...", ...}

# 成功 - 列表
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}

# 错误
{
  "code": "NOT_FOUND",
  "message": "User not found",
  "details": {}
}
```

### 3.3 认证

- 所有端点默认需要 JWT (除 `POST /auth/login`, `POST /auth/register`, `GET /health`)
- Token: `Authorization: Bearer <jwt>`
- 管理员端点: `require_admin` 依赖

### 3.4 积分追踪

LLM 调用端点在响应头中返回:
```
X-Credits-Consumed: 15
X-Credits-Remaining: 485
```

---

## 4. 数据库规范

### 4.1 迁移管理

使用 **Alembic** 管理数据库变更:

```bash
# 创建迁移
cd backend
alembic revision --autogenerate -m "add_xxx_table"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

**迁移文件命名**: `{timestamp}_{description}.py` (自动生成)

### 4.2 模型约定

```python
import uuid
from datetime import datetime, UTC
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
```

### 4.3 向量检索

```sql
-- 统一 1024 维, HNSW 索引, cosine 距离
CREATE INDEX idx_xxx_embedding ON table_name
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- 查询模式
SELECT content, 1 - (embedding <=> $1::vector) AS similarity
FROM table_name
WHERE ... 
ORDER BY embedding <=> $1::vector
LIMIT 10;
```

---

## 5. 异常处理

### 5.1 后端异常层次

```python
class BidAgentException(Exception):
    """基础异常"""
    code: str = "INTERNAL_ERROR"
    status_code: int = 500
    message: str = "Internal server error"

class NotFoundError(BidAgentException):
    code = "NOT_FOUND"
    status_code = 404
    def __init__(self, resource_type: str, resource_id: str):
        self.message = f"{resource_type} {resource_id} not found"

class ValidationError(BidAgentException):
    code = "VALIDATION_ERROR"
    status_code = 422

class AuthenticationError(BidAgentException):
    code = "AUTHENTICATION_FAILED"
    status_code = 401

class AuthorizationError(BidAgentException):
    code = "FORBIDDEN"
    status_code = 403

class InsufficientCreditsError(BidAgentException):
    code = "INSUFFICIENT_CREDITS"
    status_code = 402
    def __init__(self, required: int, available: int):
        self.message = f"Insufficient credits: need {required}, have {available}"

class LLMError(BidAgentException):
    code = "LLM_ERROR"
    status_code = 502

class CrawlerError(BidAgentException):
    code = "CRAWLER_ERROR"
    status_code = 502
```

### 5.2 全局异常处理器

```python
@app.exception_handler(BidAgentException)
async def bidagent_exception_handler(request: Request, exc: BidAgentException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )
```

---

## 6. 测试策略

### 6.1 后端测试 (pytest)

**目录结构**:
```
backend/tests/
├── conftest.py         # fixtures: async client, test db, mock LLM
├── api/                # API 集成测试
│   ├── test_auth.py
│   ├── test_projects.py
│   └── test_opportunities.py
├── services/           # Service 单元测试
│   ├── test_user_service.py
│   └── test_bid_analysis_service.py
├── agents/             # Agent/Skill 测试
│   ├── test_skills.py
│   └── test_workflow.py
└── core/               # 核心模块测试
```

**Fixtures**:
```python
# conftest.py
@pytest.fixture
async def db_session():
    """异步测试数据库 session"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(test_engine) as session:
        yield session

@pytest.fixture
async def client(db_session):
    """FastAPI TestClient"""
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

@pytest.fixture
def mock_llm():
    """Mock LLM Client"""
    with patch("app.agents.llm_client.LLMClient") as mock:
        instance = AsyncMock()
        instance.chat.return_value = LLMResponse(content="test", ...)
        mock.return_value = instance
        yield instance
```

**测试模式**:
```python
@pytest.mark.asyncio
async def test_create_project(client, auth_headers):
    response = await client.post(
        "/v1/projects",
        json={"name": "Test Project", "institution": "adb"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["status"] == "draft"
```

**覆盖率目标**: ≥ 80% (核心 services ≥ 90%)

```bash
# 运行测试
cd backend && pytest -v
cd backend && pytest --cov=app --cov-report=xml --cov-report=term-missing
```

### 6.2 前端测试 (Playwright)

**E2E 测试**:
```typescript
// tests/auth.spec.ts
test.describe("Authentication", () => {
  test("user can register and login", async ({ page }) => {
    await page.goto("/zh/auth/register")
    await page.fill('input[name="name"]', "测试用户")
    await page.fill('input[name="email"]', "test@example.com")
    await page.fill('input[name="password"]', "Password123!")
    await page.click('button:has-text("注册")')
    await expect(page).toHaveURL(/\/dashboard/)
  })
  
  test("login with valid credentials", async ({ page }) => {
    await page.goto("/zh/auth/login")
    await page.fill('input[name="email"]', "test@example.com")
    await page.fill('input[name="password"]', "Password123!")
    await page.click('button:has-text("登录")')
    await expect(page).toHaveURL(/\/dashboard/)
  })
})
```

```bash
# 运行 E2E 测试
cd frontend && npx playwright test
cd frontend && npx playwright test --ui  # 交互模式
```

---

## 7. Git 工作流

### 7.1 分支策略

```
main          ← 生产分支 (protected)
├── develop   ← 开发主分支
│   ├── feature/xxx   ← 功能分支
│   ├── fix/xxx       ← 修复分支
│   └── refactor/xxx  ← 重构分支
└── release/x.x.x    ← 发布分支
```

### 7.2 提交格式

```
<type>(<scope>): <description>

feat(crawler): add WB opportunity scraper
fix(credits): prevent negative balance on concurrent deduction
docs(api): update OpenAPI specification
refactor(auth): migrate to Zustand store
test(services): add bid analysis service tests
chore(deps): upgrade next.js to 15.1
perf(vector): optimize HNSW index parameters
```

**Type**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`

**Scope**: `auth`, `crawler`, `credits`, `api`, `agent`, `frontend`, `db`, `deps`, `ci`

### 7.3 PR 规范

- Title: 同 commit 格式
- Description: 包含变更说明 + 测试方法 + 截图 (UI 变更)
- 必须通过 CI (lint + test)
- 至少 1 reviewer approve

---

## 8. 环境配置

### 8.1 环境变量文件

开发环境使用 `.env` 文件 (不提交到 Git):

```bash
# .env (根目录, docker-compose 读取)
POSTGRES_USER=bidagent
POSTGRES_PASSWORD=bidagent_dev
POSTGRES_DB=bidagent
REDIS_URL=redis://localhost:6379/0

# backend/.env
DATABASE_URL=postgresql+asyncpg://bidagent:bidagent_dev@localhost:5432/bidagent
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-pro
EMBEDDING_API_KEY=xxx
EMBEDDING_BASE_URL=https://api.hunyuan.cloud.tencent.com
CELERY_BROKER_URL=redis://localhost:6379/1

# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 8.2 Docker Compose

```yaml
# docker-compose.yml
version: "3.9"
services:
  postgres:
    image: pgvector/pgvector:pg16
    ports: ["5432:5432"]
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

volumes:
  pgdata:
```

### 8.3 开发启动流程

```bash
# 1. 启动基础设施
docker compose up -d postgres redis

# 2. 后端
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 3. Celery Worker (新终端)
cd backend
celery -A app.tasks.celery_app worker -l info

# 4. 前端
cd frontend
npm install
npm run dev
```

---

## 9. 依赖管理

### 9.1 Python

使用 `requirements.txt` (后续可迁移到 `pyproject.toml`):

```
# 核心框架
fastapi>=0.115
uvicorn[standard]>=0.32
sqlalchemy[asyncio]>=2.0
asyncpg>=0.30
alembic>=1.14

# 认证
python-jose[cryptography]>=3.3
passlib[bcrypt]>=1.7

# AI
openai>=1.50
langgraph>=0.2
langchain-core>=0.3

# 向量
pgvector>=0.3

# 任务队列
celery[redis]>=5.4

# 工具
httpx>=0.27
pydantic>=2.9
python-multipart>=0.0.12
```

### 9.2 Node.js

使用 `package.json`:

```json
{
  "dependencies": {
    "next": "^15.0",
    "react": "^18.3",
    "react-dom": "^18.3",
    "next-intl": "^4.7",
    "@tanstack/react-query": "^5.0",
    "axios": "^1.7",
    "zustand": "^5.0",
    "lucide-react": "^0.460",
    "date-fns": "^3.6",
    "clsx": "^2.1",
    "tailwind-merge": "^2.0"
  },
  "devDependencies": {
    "typescript": "^5.6",
    "tailwindcss": "^3.4",
    "@playwright/test": "^1.58",
    "eslint": "^9.0",
    "prettier": "^3.0"
  }
}
```

---

## 10. 日志规范

### 10.1 后端日志

```python
import logging

logger = logging.getLogger(__name__)

# 级别使用
logger.debug("Processing chunk %d of %d", i, total)     # 开发调试
logger.info("Project %s analysis started", project_id)    # 正常流程
logger.warning("LLM retry %d for project %s", retry, id) # 可恢复问题
logger.error("LLM call failed: %s", str(e), exc_info=True)  # 错误
```

### 10.2 结构化日志

```python
# 生产环境使用 JSON 格式
{
  "timestamp": "2026-02-11T10:30:00Z",
  "level": "INFO",
  "logger": "app.services.bid_analysis",
  "message": "Analysis completed",
  "project_id": "uuid",
  "user_id": "uuid",
  "duration_ms": 3500,
  "tokens_consumed": 2800
}
```
