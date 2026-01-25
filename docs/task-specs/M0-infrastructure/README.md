# M0 - 基础设施任务规格书

## 概述

| 属性 | 值 |
|------|-----|
| 里程碑 | M0 - Infrastructure |
| 周期 | Week 1 |
| 任务总数 | 8 |
| Mini-Agent 任务 | 6 |
| Opus 任务 | 2 |

## 目标

- 完成项目脚手架搭建
- 配置开发环境和CI/CD
- 建立代码规范和提交流程

---

## 任务列表

---

### M0-01: 项目仓库初始化

```yaml
---
id: M0-01
title: 项目仓库初始化
executor: opus
priority: P0
estimated_hours: 2
task_type: design
dependencies: []
outputs:
  - .github/workflows/ci.yml
  - .github/PULL_REQUEST_TEMPLATE.md
  - .gitignore
  - README.md
  - LICENSE
acceptance_criteria:
  - GitHub仓库创建完成
  - Monorepo结构（frontend/backend/docs）
  - main/develop分支保护规则
  - .gitignore配置完整
  - README.md包含项目说明
---
```

#### 描述

初始化Git仓库，配置Monorepo结构，设置分支策略。

#### 输入

- 无前置依赖

#### 输出文件

```
bid_agent/
├── .github/
│   ├── workflows/
│   └── PULL_REQUEST_TEMPLATE.md
├── frontend/
├── backend/
├── docs/
├── .gitignore
├── README.md
└── LICENSE
```

#### 验收标准

- [ ] AC-1: GitHub仓库创建完成
- [ ] AC-2: Monorepo结构（frontend/backend/docs）
- [ ] AC-3: main/develop分支保护规则配置
- [ ] AC-4: .gitignore配置完整（Node、Python、IDE）
- [ ] AC-5: README.md包含项目说明和快速开始指南

---

### M0-02: 后端项目骨架

```yaml
---
id: M0-02
title: 后端项目骨架
executor: mini-agent
priority: P0
estimated_hours: 3
task_type: coding
dependencies:
  - M0-01
outputs:
  - backend/app/__init__.py
  - backend/app/main.py
  - backend/app/config.py
  - backend/app/api/v1/health.py
  - backend/app/core/logging.py
  - backend/requirements.txt
  - backend/pyproject.toml
acceptance_criteria:
  - uvicorn app.main:app --reload 可启动
  - /health 端点返回200
  - /docs Swagger文档可访问
  - 日志输出正常
---
```

#### 描述

创建FastAPI项目基础结构，配置依赖管理。

#### 输入

- 已完成的仓库结构 (M0-01)

#### 输出文件

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── health.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── logging.py
│   └── utils/
│       └── __init__.py
├── tests/
│   └── __init__.py
├── alembic/
├── requirements.txt
├── requirements-dev.txt
└── pyproject.toml
```

#### 验收标准

- [ ] AC-1: `uvicorn app.main:app --reload` 可启动
- [ ] AC-2: `/health` 端点返回200状态码
- [ ] AC-3: `/docs` Swagger文档可访问
- [ ] AC-4: 日志输出正常（INFO级别）

#### 详细步骤

1. 创建Python虚拟环境
2. 初始化FastAPI项目结构
3. 配置pyproject.toml（使用Ruff）
4. 创建目录结构
5. 实现health端点
6. 配置日志模块

#### 代码模板

**app/main.py**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import health

app = FastAPI(
    title="BidAgent API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])

@app.on_event("startup")
async def startup():
    pass

@app.on_event("shutdown")
async def shutdown():
    pass
```

**app/config.py**
```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql://localhost/bidagent"
    REDIS_URL: str = "redis://localhost:6379"
    SECRET_KEY: str = "your-secret-key"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

### M0-03: 前端项目骨架

```yaml
---
id: M0-03
title: 前端项目骨架
executor: mini-agent
priority: P0
estimated_hours: 3
task_type: coding
dependencies:
  - M0-01
outputs:
  - frontend/src/app/layout.tsx
  - frontend/src/app/page.tsx
  - frontend/package.json
  - frontend/tsconfig.json
  - frontend/tailwind.config.js
  - frontend/next.config.js
acceptance_criteria:
  - npm run dev 可启动
  - TypeScript编译无错误
  - Tailwind样式生效
  - ESLint检查通过
---
```

#### 描述

创建Next.js 15项目，配置TypeScript和Tailwind。

#### 输入

- 已完成的仓库结构 (M0-01)

#### 输出文件

```
frontend/
├── src/
│   ├── app/
│   │   ├── (auth)/
│   │   │   └── layout.tsx
│   │   ├── (main)/
│   │   │   └── layout.tsx
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── components/
│   │   └── ui/
│   ├── lib/
│   │   └── utils.ts
│   ├── hooks/
│   ├── stores/
│   └── types/
├── public/
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
├── .eslintrc.json
├── .prettierrc
└── package.json
```

#### 验收标准

- [ ] AC-1: `npm run dev` 可启动
- [ ] AC-2: TypeScript编译无错误
- [ ] AC-3: Tailwind样式生效
- [ ] AC-4: ESLint检查通过

#### 详细步骤

1. `npx create-next-app@latest frontend --typescript --tailwind --app`
2. 安装依赖包
3. 配置路径别名
4. 设置ESLint和Prettier
5. 创建基础布局

#### 依赖包

```json
{
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@tanstack/react-query": "^5.0.0",
    "zustand": "^4.5.0",
    "next-intl": "^3.0.0",
    "zod": "^3.22.0",
    "react-hook-form": "^7.50.0",
    "@hookform/resolvers": "^3.3.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "@types/react": "^18.2.0",
    "@types/node": "^20.0.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "eslint": "^8.56.0",
    "prettier": "^3.2.0"
  }
}
```

---

### M0-04: Docker开发环境

```yaml
---
id: M0-04
title: Docker开发环境
executor: mini-agent
priority: P0
estimated_hours: 2
task_type: coding
dependencies:
  - M0-01
outputs:
  - docker-compose.yml
  - scripts/init-db.sql
  - .env.example
acceptance_criteria:
  - docker compose up -d 启动成功
  - PostgreSQL可连接
  - Redis可连接
  - pgvector扩展已安装
  - 数据持久化正常
---
```

#### 描述

配置Docker Compose开发环境，包含数据库和缓存。

#### 输入

- 已完成的仓库结构 (M0-01)

#### 输出文件

```
bid_agent/
├── docker-compose.yml
├── scripts/
│   └── init-db.sql
└── .env.example
```

#### 验收标准

- [ ] AC-1: `docker compose up -d` 启动成功
- [ ] AC-2: PostgreSQL可连接 (localhost:5432)
- [ ] AC-3: Redis可连接 (localhost:6379)
- [ ] AC-4: pgvector扩展已安装
- [ ] AC-5: 数据持久化正常

#### 代码模板

**docker-compose.yml**
```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: bidagent-postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: bidagent
      POSTGRES_PASSWORD: bidagent123
      POSTGRES_DB: bidagent
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U bidagent"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: bidagent-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio
    container_name: bidagent-minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

**scripts/init-db.sql**
```sql
-- 启用扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 创建schema
CREATE SCHEMA IF NOT EXISTS bidagent;
```

---

### M0-05: CI/CD Pipeline

```yaml
---
id: M0-05
title: CI/CD Pipeline
executor: opus
priority: P1
estimated_hours: 3
task_type: design
dependencies:
  - M0-02
  - M0-03
outputs:
  - .github/workflows/ci.yml
  - .github/workflows/deploy.yml
acceptance_criteria:
  - PR触发lint和测试
  - main分支合并触发部署
  - 测试覆盖率报告
  - 构建缓存配置
---
```

#### 描述

配置GitHub Actions工作流，实现自动化测试和部署。

#### 输入

- 后端项目骨架 (M0-02)
- 前端项目骨架 (M0-03)

#### 输出文件

```
.github/
└── workflows/
    ├── ci.yml
    └── deploy.yml
```

#### 验收标准

- [ ] AC-1: PR触发lint和测试
- [ ] AC-2: main分支合并触发部署
- [ ] AC-3: 测试覆盖率报告生成
- [ ] AC-4: 构建缓存配置正确

---

### M0-06: 数据库迁移配置

```yaml
---
id: M0-06
title: 数据库迁移配置
executor: mini-agent
priority: P1
estimated_hours: 2
task_type: coding
dependencies:
  - M0-02
  - M0-04
outputs:
  - backend/alembic.ini
  - backend/alembic/env.py
  - backend/alembic/script.py.mako
  - backend/alembic/versions/.gitkeep
acceptance_criteria:
  - alembic revision --autogenerate 可用
  - alembic upgrade head 可执行
  - 迁移脚本版本化
---
```

#### 描述

配置Alembic数据库迁移工具。

#### 输入

- 后端项目骨架 (M0-02)
- Docker环境 (M0-04)

#### 输出文件

```
backend/
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
└── alembic.ini
```

#### 验收标准

- [ ] AC-1: `alembic revision --autogenerate` 可用
- [ ] AC-2: `alembic upgrade head` 可执行
- [ ] AC-3: 迁移脚本版本化管理

#### 代码模板

**alembic/env.py (关键部分)**
```python
from app.config import settings
from app.models import Base

target_metadata = Base.metadata

def run_migrations_online():
    connectable = create_engine(settings.DATABASE_URL)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()
```

---

### M0-07: shadcn/ui组件库配置

```yaml
---
id: M0-07
title: shadcn/ui组件库配置
executor: mini-agent
priority: P1
estimated_hours: 2
task_type: coding
dependencies:
  - M0-03
outputs:
  - frontend/components.json
  - frontend/src/components/ui/button.tsx
  - frontend/src/components/ui/input.tsx
  - frontend/src/components/ui/card.tsx
  - frontend/src/lib/utils.ts
acceptance_criteria:
  - Button组件可正常使用
  - 暗色模式切换正常
  - 组件样式符合设计规范
---
```

#### 描述

配置shadcn/ui，安装基础组件。

#### 输入

- 前端项目骨架 (M0-03)

#### 输出文件

```
frontend/
├── components.json
└── src/
    ├── components/
    │   └── ui/
    │       ├── button.tsx
    │       ├── input.tsx
    │       ├── card.tsx
    │       ├── dialog.tsx
    │       ├── dropdown-menu.tsx
    │       ├── toast.tsx
    │       ├── form.tsx
    │       ├── table.tsx
    │       ├── tabs.tsx
    │       └── avatar.tsx
    └── lib/
        └── utils.ts
```

#### 验收标准

- [ ] AC-1: Button组件可正常使用
- [ ] AC-2: 暗色模式切换正常
- [ ] AC-3: 组件样式符合设计规范

#### 详细步骤

1. `npx shadcn-ui@latest init`
2. 安装基础组件: button, input, card, dialog, dropdown-menu, toast
3. 配置主题色
4. 创建组件索引

#### 需安装组件

```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add input
npx shadcn-ui@latest add card
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add form
npx shadcn-ui@latest add table
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add avatar
```

---

### M0-08: 开发环境文档

```yaml
---
id: M0-08
title: 开发环境文档
executor: mini-agent
priority: P2
estimated_hours: 1
task_type: documentation
dependencies:
  - M0-02
  - M0-03
  - M0-04
outputs:
  - docs/development-environment.md
  - docs/troubleshooting.md
acceptance_criteria:
  - 新成员可按文档完成环境搭建
  - 包含常见问题解答
  - IDE配置说明
---
```

#### 描述

编写开发环境搭建指南。

#### 输入

- 后端项目骨架 (M0-02)
- 前端项目骨架 (M0-03)
- Docker环境 (M0-04)

#### 输出文件

- `docs/development-environment.md`
- `docs/troubleshooting.md`

#### 验收标准

- [ ] AC-1: 新成员可按文档完成环境搭建
- [ ] AC-2: 包含常见问题解答
- [ ] AC-3: IDE配置说明完整

---

## 里程碑检查点

### 完成标准

- [ ] 所有任务完成
- [ ] 前后端可本地启动
- [ ] CI流程正常运行
- [ ] 数据库可连接
- [ ] 团队成员环境搭建完成

### 交付物

1. 可运行的项目骨架
2. Docker开发环境
3. CI/CD Pipeline
4. 开发文档

---

## 风险与依赖

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| Docker兼容性问题 | 中 | 中 | 提供备选本地安装方案 |
| Node/Python版本冲突 | 低 | 低 | 使用nvm/pyenv管理版本 |

---

> 📝 **文档版本**: 2.0 | **更新日期**: 2026-01-25 | **变更**: 添加 YAML Front Matter，统一验收标准格式
