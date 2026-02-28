# AGENTS.md

Guidelines for AI coding agents working in this repository.

## Project Overview

BidAgent V2: AI-powered bidding platform for multilateral development banks (ADB, WB, UN).
Core workflow: **Opportunity Crawling → TOR/RFP Analysis → AI-Guided Proposal Writing**

**Status**: V2 rebuild — development docs complete, code TBD.

**Stack**: Next.js 15 + FastAPI + PostgreSQL 16 (pgvector) + Redis + LangGraph + DeepSeek

## V2 Development Docs

All design documents are in `docs/v2/`. **Read these before writing any code:**

| Doc | Purpose |
|-----|---------|
| `docs/v2/01-prd.md` | Product requirements, user flows, feature priority |
| `docs/v2/02-architecture.md` | System architecture, 3-layer Agent (MCP + Skills + LangGraph) |
| `docs/v2/03-data-model.md` | 34 tables, enums, vector indexes, ER diagram |
| `docs/v2/04-openapi.md` | 97 API endpoints with request/response schemas |
| `docs/v2/05-agent-workflow.md` | LLM Client, Skills, LangGraph workflow, RAG, prompts |
| `docs/v2/06-frontend-design.md` | Routes, components, Zustand, TanStack Query, SSE |
| `docs/v2/07-dev-standards.md` | Code style, Git workflow, testing, environment |

## Build/Lint/Test Commands

### Backend (Python)

```bash
cd backend && uvicorn app.main:app --reload  # Start dev server :8000
cd backend && ruff check .                    # Lint
cd backend && ruff check --fix .              # Auto-fix lint issues
cd backend && pytest -v                       # All tests
cd backend && pytest tests/api/test_users.py -v  # Single file
cd backend && pytest --cov=app --cov-report=xml  # With coverage
```

### Frontend (TypeScript)

```bash
cd frontend && npm run dev       # Start dev server :3000
cd frontend && npm run build     # Production build
cd frontend && npm run lint      # ESLint
cd frontend && npx playwright test  # E2E tests
```

### Infrastructure

```bash
docker compose up -d postgres redis  # Start databases
```

## Code Style Guidelines

### Python (Backend)

- **Formatter**: Ruff (line-length: 88)
- **Imports**: Absolute, grouped: stdlib → third-party → local
- **Type hints**: Required for all public APIs
- **Naming**: `snake_case` functions/vars, `PascalCase` classes, `UPPER_SNAKE_CASE` constants
- **Async**: Use `asyncio.gather()` for parallel ops, avoid blocking I/O
- **Errors**: Inherit from `BidAgentException` with `code` and `message`
- **Dates**: `datetime.now(UTC)` — never `datetime.utcnow()`
- **IDs**: UUID v4 for all primary keys

### TypeScript (Frontend)

- **Formatter**: Prettier (semi: false, singleQuote: false, tabWidth: 2)
- **Naming**: `kebab-case` files, `camelCase` functions, `PascalCase` components
- **Types**: No `any` — use `unknown` or explicit types
- **i18n**: All UI text through `next-intl`, never hardcode strings
- **Components**: Function components + `memo()`, explicit Props interfaces
- **State**: Zustand for global state, TanStack Query for server state

## Git Commits

Format: `<type>(<scope>): <description>`

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`

```bash
feat(crawler): add WB opportunity scraper
fix(credits): prevent negative balance on concurrent deduction
```

## Key Architecture Patterns

### Backend Service Layer

```python
# services/user_service.py
class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

# api/v1/users.py — inject service
@router.get("/{user_id}")
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    return await service.get_by_id(user_id)
```

### 3-Layer Agent Architecture

```
MCP Tools (data retrieval) → Skills (analysis units) → LangGraph Workflows (orchestration)
```

- **MCP Tools**: `knowledge_search`, `bid_document_search`, `opportunity_query`
- **Skills**: `AnalyzeQualification`, `EvaluateCriteria`, `SectionGuidance`, `ReviewDraft`, `QualityReview`, etc.
- **LangGraph**: Bid guidance workflow with `RedisSaver` checkpoint (analyze → guide → review)

### LLM Integration

- All LLM calls via `agents/llm_client.py` (AsyncOpenAI wrapper for DeepSeek)
- Track credits via `X-Credits-Consumed` / `X-Credits-Remaining` headers
- Embedding: `ResilientEmbeddingClient` (Tencent Hunyuan primary, Zhipu fallback)

### Crawler Pattern

```python
class ADBCrawler(BaseCrawler):
    source_name = "adb"
    base_url = "https://www.adb.org"
    async def fetch_list(self, page: int = 1) -> list[TenderInfo]: ...
    async def fetch_detail(self, tender_id: str) -> TenderInfo: ...
```

## Important Paths

| Purpose | Path |
|---------|------|
| V2 design docs | `docs/v2/` |
| API routes | `backend/app/api/v1/` |
| SQLAlchemy models | `backend/app/models/` |
| Business logic | `backend/app/services/` |
| LangGraph agents | `backend/app/agents/` |
| React pages | `frontend/src/app/[locale]/` |
| React components | `frontend/src/components/` |
| Zustand stores | `frontend/src/stores/` |
| API services | `frontend/src/services/` |

## Common Tasks

### Adding a new API endpoint

1. Define schema in `backend/app/schemas/{entity}.py`
2. Add service in `backend/app/services/{entity}_service.py`
3. Create route in `backend/app/api/v1/{entity}.py`
4. Register router in `backend/app/api/v1/__init__.py`
5. Update `docs/v2/04-openapi.md`

### Adding a LangGraph agent node

1. Review `docs/v2/05-agent-workflow.md`
2. Create node in `agents/workflows/{workflow}/nodes/`
3. Update graph in `agents/workflows/{workflow}/graph.py`
4. Add prompts in `agents/prompts/templates/`

## Testing Patterns

### Backend (pytest)

```python
@pytest.mark.asyncio
async def test_create_user(client):
    response = await client.post("/api/v1/users", json={"email": "test@example.com"})
    assert response.status_code == 201
```

### Frontend (Playwright)

```typescript
test("user can login", async ({ page }) => {
  await page.goto("/login")
  await page.fill('input[name="email"]', "test@example.com")
  await page.click('button:has-text("Login")')
  await expect(page).toHaveURL("/dashboard")
})
```

## Environment Variables

Key configs (define in `.env`): `DATABASE_URL`, `REDIS_URL`, `DEEPSEEK_API_KEY`, `JWT_SECRET_KEY`, `EMBEDDING_API_KEY`

See `docs/v2/02-architecture.md` §7 for complete env var reference.
