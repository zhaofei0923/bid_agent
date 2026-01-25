# M8 - 测试与部署任务规格书

## 概述
| 属性 | 值 |
|------|-----|
| 里程碑 | M8 - Testing & Deployment |
| 周期 | Week 12 |
| 任务总数 | 10 |
| Opus 4.5 任务 | 2 |
| Mini-Agent 任务 | 8 |

## 目标
- 完成单元测试覆盖
- 完成集成测试
- 配置CI/CD流水线
- 完成生产环境部署

---

## 任务列表

### M8-01: 测试策略设计 (Opus 4.5)
**优先级**: P0  
**预估时间**: 3小时  
**执行者**: Opus 4.5

#### 描述
设计完整的测试策略和覆盖要求。

#### 测试金字塔
```
         ┌───────────┐
         │   E2E     │  10%  Playwright
         │   Tests   │
         ├───────────┤
         │Integration│  30%  pytest + httpx
         │   Tests   │
         ├───────────┤
         │   Unit    │  60%  pytest + jest
         │   Tests   │
         └───────────┘
```

#### 覆盖率要求
| 模块 | 目标覆盖率 | 优先级 |
|------|-----------|--------|
| 核心服务 (services/) | > 80% | P0 |
| API路由 (api/) | > 70% | P0 |
| Agent工作流 | > 60% | P1 |
| 前端组件 | > 50% | P2 |
| 工具函数 | > 90% | P0 |

#### 验收标准
- [ ] 测试策略文档
- [ ] 覆盖率目标定义
- [ ] 测试环境规划

#### 输出文件
- `docs/testing-strategy.md`

---

### M8-02: 后端单元测试 (Mini-Agent)
**优先级**: P0  
**预估时间**: 6小时  
**执行者**: Mini-Agent

#### 描述
为后端核心模块编写单元测试。

#### 代码实现
```python
# tests/conftest.py
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.core.config import settings

# 测试数据库
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client."""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture
async def authenticated_client(client: AsyncClient, db_session: AsyncSession):
    """Create an authenticated test client."""
    from app.models import User
    from app.core.security import create_access_token
    
    user = User(
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User",
        is_active=True,
        credits_balance=1000,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    token = create_access_token(data={"sub": str(user.id)})
    client.headers["Authorization"] = f"Bearer {token}"
    
    return client, user


# tests/services/test_credit_service.py
import pytest
from app.services.credit_service import CreditService
from app.exceptions import InsufficientCreditsError

class TestCreditService:
    """积分服务测试"""
    
    @pytest.mark.asyncio
    async def test_get_balance(self, db_session, authenticated_client):
        """测试获取余额"""
        client, user = authenticated_client
        service = CreditService(db_session)
        
        balance = await service.get_balance(str(user.id))
        assert balance == 1000
    
    @pytest.mark.asyncio
    async def test_deduct_credits_success(self, db_session, authenticated_client):
        """测试扣费成功"""
        client, user = authenticated_client
        service = CreditService(db_session)
        
        transaction = await service.deduct_credits(
            user_id=str(user.id),
            amount=100,
            transaction_type="test",
            description="测试扣费"
        )
        
        assert transaction.amount == -100
        assert transaction.balance_after == 900
        
        new_balance = await service.get_balance(str(user.id))
        assert new_balance == 900
    
    @pytest.mark.asyncio
    async def test_deduct_credits_insufficient(self, db_session, authenticated_client):
        """测试余额不足"""
        client, user = authenticated_client
        service = CreditService(db_session)
        
        with pytest.raises(InsufficientCreditsError) as exc_info:
            await service.deduct_credits(
                user_id=str(user.id),
                amount=2000,  # 超过余额
                transaction_type="test",
                description="测试扣费"
            )
        
        assert exc_info.value.required == 2000
        assert exc_info.value.available == 1000
    
    @pytest.mark.asyncio
    async def test_concurrent_deductions(self, db_session, authenticated_client):
        """测试并发扣费"""
        import asyncio
        client, user = authenticated_client
        
        async def deduct_50():
            service = CreditService(db_session)
            try:
                await service.deduct_credits(
                    user_id=str(user.id),
                    amount=50,
                    transaction_type="test",
                    description="并发测试"
                )
                return True
            except InsufficientCreditsError:
                return False
        
        # 并发20次扣50，总共1000，应该全部成功
        results = await asyncio.gather(*[deduct_50() for _ in range(20)])
        
        assert sum(results) == 20
        
        service = CreditService(db_session)
        balance = await service.get_balance(str(user.id))
        assert balance == 0


# tests/api/test_auth.py
import pytest

class TestAuthAPI:
    """认证API测试"""
    
    @pytest.mark.asyncio
    async def test_register(self, client):
        """测试注册"""
        response = await client.post("/api/v1/auth/register", json={
            "email": "new@example.com",
            "password": "StrongPass123!",
            "full_name": "New User"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@example.com"
        assert "password" not in data
    
    @pytest.mark.asyncio
    async def test_login_success(self, client, db_session):
        """测试登录成功"""
        from app.models import User
        from app.core.security import get_password_hash
        
        user = User(
            email="login@example.com",
            hashed_password=get_password_hash("TestPass123!"),
            full_name="Login User",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        
        response = await client.post("/api/v1/auth/login", data={
            "username": "login@example.com",
            "password": "TestPass123!"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, db_session):
        """测试密码错误"""
        from app.models import User
        from app.core.security import get_password_hash
        
        user = User(
            email="wrong@example.com",
            hashed_password=get_password_hash("RightPass123!"),
            full_name="Wrong User",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        
        response = await client.post("/api/v1/auth/login", data={
            "username": "wrong@example.com",
            "password": "WrongPass123!"
        })
        
        assert response.status_code == 401
```

#### 验收标准
- [ ] 核心服务测试覆盖 > 80%
- [ ] API路由测试覆盖 > 70%
- [ ] 所有测试通过
- [ ] 测试报告生成

#### 依赖
- M8-01, M0-08

---

### M8-03: 前端单元测试 (Mini-Agent)
**优先级**: P1  
**预估时间**: 4小时  
**执行者**: Mini-Agent

#### 描述
为前端核心组件编写单元测试。

#### 代码实现
```typescript
// __tests__/components/credits/CreditBalance.test.tsx
import { render, screen, waitFor } from "@testing-library/react"
import { CreditBalance } from "@/components/credits/CreditBalance"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { vi } from "vitest"

// Mock hooks
vi.mock("@/hooks/useCredits", () => ({
  useCredits: () => ({
    balance: 500,
    isLoading: false,
    refetch: vi.fn(),
  }),
}))

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

describe("CreditBalance", () => {
  const queryClient = new QueryClient()
  
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
  
  it("displays balance", () => {
    render(<CreditBalance />, { wrapper })
    expect(screen.getByText("500")).toBeInTheDocument()
  })
  
  it("shows low balance warning", () => {
    vi.mocked(useCredits).mockReturnValue({
      balance: 50,
      isLoading: false,
      refetch: vi.fn(),
    })
    
    render(<CreditBalance />, { wrapper })
    expect(screen.getByText("lowBalanceWarning")).toBeInTheDocument()
  })
})


// __tests__/hooks/useAuth.test.ts
import { renderHook, act, waitFor } from "@testing-library/react"
import { useAuth } from "@/hooks/useAuth"
import { vi } from "vitest"

describe("useAuth", () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })
  
  it("initializes with null user", () => {
    const { result } = renderHook(() => useAuth())
    expect(result.current.user).toBeNull()
    expect(result.current.isAuthenticated).toBe(false)
  })
  
  it("login sets user and token", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        access_token: "test-token",
        user: { id: "1", email: "test@example.com" }
      }),
    })
    
    const { result } = renderHook(() => useAuth())
    
    await act(async () => {
      await result.current.login("test@example.com", "password")
    })
    
    expect(result.current.isAuthenticated).toBe(true)
    expect(localStorage.getItem("access_token")).toBe("test-token")
  })
  
  it("logout clears user and token", () => {
    localStorage.setItem("access_token", "test-token")
    
    const { result } = renderHook(() => useAuth())
    
    act(() => {
      result.current.logout()
    })
    
    expect(result.current.user).toBeNull()
    expect(localStorage.getItem("access_token")).toBeNull()
  })
})
```

#### 验收标准
- [ ] 关键组件测试
- [ ] Hooks测试
- [ ] 覆盖率 > 50%
- [ ] 测试通过

#### 依赖
- M8-01, M7-14

---

### M8-04: 集成测试 (Mini-Agent)
**优先级**: P0  
**预估时间**: 4小时  
**执行者**: Mini-Agent

#### 描述
编写关键流程集成测试。

#### 代码实现
```python
# tests/integration/test_bid_generation_flow.py
import pytest
from httpx import AsyncClient

class TestBidGenerationFlow:
    """标书生成完整流程测试"""
    
    @pytest.mark.asyncio
    async def test_full_generation_flow(self, authenticated_client):
        """测试完整的标书生成流程"""
        client, user = authenticated_client
        
        # 1. 创建项目
        project_response = await client.post("/api/v1/projects", json={
            "name": "Test Project",
            "description": "Integration test project"
        })
        assert project_response.status_code == 201
        project = project_response.json()
        project_id = project["id"]
        
        # 2. 上传TOR文档
        with open("tests/fixtures/sample_tor.pdf", "rb") as f:
            upload_response = await client.post(
                f"/api/v1/documents/upload",
                files={"file": ("tor.pdf", f, "application/pdf")},
                data={"project_id": project_id, "doc_type": "tor"}
            )
        assert upload_response.status_code == 201
        
        # 3. 等待文档解析
        import asyncio
        await asyncio.sleep(2)  # 等待异步处理
        
        # 4. 启动生成
        generate_response = await client.post(
            f"/api/v1/projects/{project_id}/generate",
            json={"language": "zh"}
        )
        assert generate_response.status_code == 200
        
        # 5. 轮询状态直到完成或等待审核
        for _ in range(30):  # 最多等待90秒
            status_response = await client.get(
                f"/api/v1/projects/{project_id}/generate/status"
            )
            status = status_response.json()
            
            if status["waiting_for_review"]:
                # 提交审核通过
                await client.post(
                    f"/api/v1/projects/{project_id}/generate/review",
                    json={"decision": "approved", "comments": ""}
                )
            
            if status["status"] == "completed":
                break
            
            await asyncio.sleep(3)
        
        # 6. 验证结果
        final_status = (await client.get(
            f"/api/v1/projects/{project_id}/generate/status"
        )).json()
        
        assert final_status["status"] == "completed"
        assert len(final_status.get("errors", [])) == 0


# tests/integration/test_credit_deduction.py
class TestCreditDeduction:
    """积分扣费集成测试"""
    
    @pytest.mark.asyncio
    async def test_llm_call_deducts_credits(self, authenticated_client):
        """测试LLM调用扣费"""
        client, user = authenticated_client
        initial_balance = user.credits_balance
        
        # 触发一个需要LLM调用的操作
        response = await client.post("/api/v1/projects/{id}/analyze", json={
            "project_id": "test-project"
        })
        
        # 检查余额变化
        balance_response = await client.get("/api/v1/credits/balance")
        new_balance = balance_response.json()["balance"]
        
        assert new_balance < initial_balance
        
        # 检查交易记录
        transactions_response = await client.get("/api/v1/credits/transactions")
        transactions = transactions_response.json()["items"]
        
        assert len(transactions) > 0
        assert transactions[0]["transaction_type"] == "llm_usage"
```

#### 验收标准
- [ ] 关键流程覆盖
- [ ] 端到端测试
- [ ] 错误场景测试
- [ ] 测试通过

#### 依赖
- M8-02

---

### M8-05: E2E测试 (Mini-Agent)
**优先级**: P2  
**预估时间**: 4小时  
**执行者**: Mini-Agent

#### 描述
使用Playwright编写端到端测试。

#### 代码实现
```typescript
// e2e/auth.spec.ts
import { test, expect } from "@playwright/test"

test.describe("Authentication", () => {
  test("user can register and login", async ({ page }) => {
    // 注册
    await page.goto("/register")
    await page.fill('[name="email"]', "e2e@example.com")
    await page.fill('[name="password"]', "TestPass123!")
    await page.fill('[name="full_name"]', "E2E User")
    await page.click('button[type="submit"]')
    
    // 应跳转到登录页
    await expect(page).toHaveURL(/\/login/)
    
    // 登录
    await page.fill('[name="email"]', "e2e@example.com")
    await page.fill('[name="password"]', "TestPass123!")
    await page.click('button[type="submit"]')
    
    // 应跳转到仪表盘
    await expect(page).toHaveURL(/\/dashboard/)
    await expect(page.locator("text=E2E User")).toBeVisible()
  })
  
  test("shows error on invalid credentials", async ({ page }) => {
    await page.goto("/login")
    await page.fill('[name="email"]', "wrong@example.com")
    await page.fill('[name="password"]', "WrongPass123!")
    await page.click('button[type="submit"]')
    
    await expect(page.locator("text=认证失败")).toBeVisible()
  })
})


// e2e/project.spec.ts
test.describe("Project Management", () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto("/login")
    await page.fill('[name="email"]', "test@example.com")
    await page.fill('[name="password"]', "TestPass123!")
    await page.click('button[type="submit"]')
    await page.waitForURL(/\/dashboard/)
  })
  
  test("user can create a project", async ({ page }) => {
    await page.goto("/dashboard/projects/new")
    
    await page.fill('[name="name"]', "E2E Test Project")
    await page.fill('[name="description"]', "Created by E2E test")
    
    // 上传文档
    await page.setInputFiles(
      'input[type="file"]',
      "e2e/fixtures/sample_tor.pdf"
    )
    
    await page.click('button:has-text("创建项目")')
    
    await expect(page).toHaveURL(/\/dashboard\/projects\/[\w-]+/)
    await expect(page.locator("text=E2E Test Project")).toBeVisible()
  })
})
```

#### 验收标准
- [ ] 核心用户流程
- [ ] 跨浏览器测试
- [ ] CI集成
- [ ] 截图/录制

#### 依赖
- M8-04

---

### M8-06: CI/CD流水线配置 (Opus 4.5)
**优先级**: P0  
**预估时间**: 4小时  
**执行者**: Opus 4.5

#### 描述
配置完整的CI/CD流水线。

#### GitHub Actions配置
```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: "3.11"
  NODE_VERSION: "20"

jobs:
  # === 后端测试 ===
  backend-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: bidagent_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        working-directory: backend
        run: |
          pip install poetry
          poetry install
      
      - name: Run linting
        working-directory: backend
        run: |
          poetry run ruff check .
          poetry run ruff format --check .
      
      - name: Run tests
        working-directory: backend
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/bidagent_test
          REDIS_URL: redis://localhost:6379
        run: |
          poetry run pytest --cov=app --cov-report=xml --cov-report=html
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: backend/coverage.xml
          flags: backend

  # === 前端测试 ===
  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: "pnpm"
      
      - name: Install pnpm
        run: npm install -g pnpm
      
      - name: Install dependencies
        working-directory: frontend
        run: pnpm install
      
      - name: Run linting
        working-directory: frontend
        run: pnpm lint
      
      - name: Run type check
        working-directory: frontend
        run: pnpm type-check
      
      - name: Run tests
        working-directory: frontend
        run: pnpm test --coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: frontend/coverage/lcov.info
          flags: frontend

  # === E2E测试 ===
  e2e-test:
    runs-on: ubuntu-latest
    needs: [backend-test, frontend-test]
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
      
      - name: Install dependencies
        run: |
          cd frontend && pnpm install
          npx playwright install --with-deps
      
      - name: Start services
        run: |
          docker compose -f docker-compose.test.yml up -d
          sleep 30  # 等待服务启动
      
      - name: Run E2E tests
        run: cd frontend && pnpm e2e
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: frontend/playwright-report/

  # === 构建 Docker 镜像 ===
  build:
    runs-on: ubuntu-latest
    needs: [backend-test, frontend-test]
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push backend
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: ghcr.io/${{ github.repository }}/backend:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      - name: Build and push frontend
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: ghcr.io/${{ github.repository }}/frontend:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # === 部署 ===
  deploy:
    runs-on: ubuntu-latest
    needs: [build, e2e-test]
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - name: Deploy to production
        run: |
          echo "Deploying to production..."
          # 使用SSH或K8s部署
```

#### 验收标准
- [ ] 测试自动运行
- [ ] 覆盖率报告
- [ ] 镜像自动构建
- [ ] 部署流水线

---

### M8-07: 生产环境部署 (Mini-Agent)
**优先级**: P0  
**预估时间**: 4小时  
**执行者**: Mini-Agent

#### 描述
配置生产环境部署方案。

#### Docker Compose生产配置
```yaml
# docker-compose.prod.yml
version: "3.8"

services:
  backend:
    image: ghcr.io/your-org/bidagent-backend:latest
    restart: always
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - MINIO_ENDPOINT=${MINIO_ENDPOINT}
      - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
      - MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  frontend:
    image: ghcr.io/your-org/bidagent-frontend:latest
    restart: always
    environment:
      - NEXT_PUBLIC_API_URL=${API_URL}
    ports:
      - "3000:3000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  celery-worker:
    image: ghcr.io/your-org/bidagent-backend:latest
    restart: always
    command: celery -A app.celery_app worker -l info -Q default,crawler
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    depends_on:
      - redis
      - db
  
  celery-beat:
    image: ghcr.io/your-org/bidagent-backend:latest
    restart: always
    command: celery -A app.celery_app beat -l info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - redis
  
  db:
    image: postgres:16
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=${DB_NAME}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
  
  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
  
  minio:
    image: minio/minio
    restart: always
    volumes:
      - minio_data:/data
    environment:
      - MINIO_ROOT_USER=${MINIO_ACCESS_KEY}
      - MINIO_ROOT_PASSWORD=${MINIO_SECRET_KEY}
    command: server /data --console-address ":9001"
  
  nginx:
    image: nginx:alpine
    restart: always
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

#### 验收标准
- [ ] 服务正常启动
- [ ] HTTPS配置
- [ ] 健康检查
- [ ] 日志收集

#### 依赖
- M8-06

---

### M8-08: 监控告警配置 (Mini-Agent)
**优先级**: P1  
**预估时间**: 3小时  
**执行者**: Mini-Agent

#### 描述
配置应用监控和告警。

#### 验收标准
- [ ] Prometheus指标
- [ ] Grafana仪表盘
- [ ] 错误告警
- [ ] 性能监控

#### 依赖
- M8-07

---

### M8-09: 安全扫描 (Mini-Agent)
**优先级**: P1  
**预估时间**: 2小时  
**执行者**: Mini-Agent

#### 描述
配置安全扫描流程。

#### 代码实现
```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  schedule:
    - cron: "0 0 * * 1"  # 每周一
  push:
    branches: [main]

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Python dependency scan
        uses: snyk/actions/python@master
        with:
          command: test
          args: --file=backend/pyproject.toml
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      
      - name: Node dependency scan
        uses: snyk/actions/node@master
        with:
          command: test
          args: --file=frontend/package.json
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
  
  code-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: CodeQL Analysis
        uses: github/codeql-action/analyze@v3
        with:
          languages: python, javascript
  
  container-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build backend image
        run: docker build -t backend:scan ./backend
      
      - name: Scan backend image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: backend:scan
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
```

#### 验收标准
- [ ] 依赖扫描
- [ ] 代码扫描
- [ ] 容器扫描
- [ ] 报告生成

#### 依赖
- M8-06

---

### M8-10: 发布文档 (Mini-Agent)
**优先级**: P2  
**预估时间**: 2小时  
**执行者**: Mini-Agent

#### 描述
编写发布和运维文档。

#### 验收标准
- [ ] 部署手册
- [ ] 运维手册
- [ ] 故障排查指南
- [ ] 版本发布流程

#### 依赖
- M8-07

---

## 里程碑检查点

### 完成标准
- [ ] 测试覆盖率达标
- [ ] CI/CD流水线可用
- [ ] 生产环境部署成功
- [ ] 监控告警配置完成

### 交付物
1. 测试报告
2. CI/CD配置
3. 部署文档
4. 监控仪表盘

---

## 部署架构

```
                    ┌─────────────┐
                    │   CDN       │
                    │  (可选)     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Nginx     │
                    │  (反向代理)  │
                    └──────┬──────┘
                           │
           ┌───────────────┴───────────────┐
           │                               │
    ┌──────▼──────┐                 ┌──────▼──────┐
    │  Frontend   │                 │   Backend   │
    │  (Next.js)  │                 │  (FastAPI)  │
    └─────────────┘                 └──────┬──────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
             ┌──────▼──────┐        ┌──────▼──────┐        ┌──────▼──────┐
             │ PostgreSQL  │        │    Redis    │        │    MinIO    │
             │   + pgvector│        │   (Cache)   │        │  (Storage)  │
             └─────────────┘        └─────────────┘        └─────────────┘
```
