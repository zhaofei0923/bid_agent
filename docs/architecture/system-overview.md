# BidAgent 系统架构

## 1. 架构概览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              客户端层 (Client Layer)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   Web Browser   │  │   Mobile (PWA)  │  │   API Client    │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
└───────────┼─────────────────────┼─────────────────────┼─────────────────────┘
            │                     │                     │
            └──────────────────────┼──────────────────────┘
                                  │ HTTPS
┌─────────────────────────────────┼───────────────────────────────────────────┐
│                        Cloudflare (CDN + WAF)                               │
└─────────────────────────────────┼───────────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼───────────────────────────────────────────┐
│                              Nginx                                          │
│                    (反向代理 + 负载均衡 + SSL)                                │
└─────────────┬───────────────────┼───────────────────────────────────────────┘
              │                   │
              ▼                   ▼
┌─────────────────────┐  ┌─────────────────────────────────────────────────────┐
│    Next.js 前端     │  │                   FastAPI 后端                       │
│   (SSR + Static)    │  │                                                     │
│                     │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  ├─ /app            │  │  │  Auth   │ │Crawler  │ │  LLM    │ │Document │   │
│  │  ├─ (auth)       │  │  │ Module  │ │ Module  │ │ Service │ │ Service │   │
│  │  ├─ dashboard    │  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘   │
│  │  ├─ projects     │  │       │           │           │           │         │
│  │  ├─ documents    │  │  ┌────┴───────────┴───────────┴───────────┴────┐   │
│  │  └─ settings     │  │  │              Core Business Logic            │   │
│  │                   │  │  │    (BidAgent Workflow / LangGraph)         │   │
│  └─ /api (BFF)      │  │  └─────────────────────────────────────────────┘   │
└─────────────────────┘  └─────────────────────────────────────────────────────┘
              │                   │
              │                   │
              ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据层 (Data Layer)                            │
├─────────────────────┬─────────────────────┬─────────────────────────────────┤
│    PostgreSQL 16    │       Redis 7       │         MinIO / S3              │
│   (主数据库+向量)    │    (缓存+会话)       │      (文件存储)                  │
│                     │                     │                                 │
│ ├─ users            │ ├─ session:*        │ ├─ /documents/                  │
│ ├─ projects         │ ├─ cache:*          │ ├─ /generated/                  │
│ ├─ documents        │ ├─ rate_limit:*     │ └─ /templates/                  │
│ ├─ bid_opportunities│ └─ queue:*          │                                 │
│ ├─ embeddings       │                     │                                 │
│ └─ credit_txns      │                     │                                 │
└─────────────────────┴─────────────────────┴─────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           外部服务 (External Services)                       │
├─────────────────────┬─────────────────────┬─────────────────────────────────┤
│   DeepSeek API      │    ADB Website      │      Payment Gateway            │
│   (LLM Provider)    │    (数据源)          │      (Stripe/支付宝)            │
└─────────────────────┴─────────────────────┴─────────────────────────────────┘
```

## 2. 技术选型详解

### 2.1 前端技术栈

| 技术 | 版本 | 用途 | 选型理由 |
|------|------|------|---------|
| **Next.js** | 15.x | 全栈框架 | App Router、Server Components、API Routes |
| **TypeScript** | 5.x | 类型安全 | 减少运行时错误 |
| **Tailwind CSS** | 3.x | 样式方案 | 高效开发、一致性 |
| **shadcn/ui** | latest | 组件库 | 高质量、可定制、无运行时依赖 |
| **TanStack Query** | 5.x | 数据获取 | 缓存、乐观更新、后台刷新 |
| **Zustand** | 4.x | 状态管理 | 轻量、简单、TypeScript友好 |
| **next-intl** | 3.x | 国际化 | Next.js最佳i18n方案 |
| **React Hook Form** | 7.x | 表单处理 | 性能优秀、验证灵活 |
| **Zod** | 3.x | 数据验证 | 运行时类型校验 |

### 2.2 后端技术栈

| 技术 | 版本 | 用途 | 选型理由 |
|------|------|------|---------|
| **FastAPI** | 0.110+ | Web框架 | 高性能、自动文档、类型提示 |
| **Python** | 3.11+ | 编程语言 | AI/ML生态丰富 |
| **SQLAlchemy** | 2.x | ORM | 成熟稳定、异步支持 |
| **Alembic** | 1.x | 数据库迁移 | SQLAlchemy配套 |
| **Pydantic** | 2.x | 数据验证 | FastAPI核心依赖 |
| **LangChain** | 0.2+ | LLM框架 | 工具丰富、社区活跃 |
| **LangGraph** | 0.1+ | 工作流引擎 | 状态机、可视化调试 |
| **Celery** | 5.x | 任务队列 | 异步任务处理 |
| **httpx** | 0.27+ | HTTP客户端 | 异步支持、现代API |

### 2.3 数据层

| 技术 | 版本 | 用途 | 配置 |
|------|------|------|------|
| **PostgreSQL** | 16 | 主数据库 | 主从复制、连接池 |
| **pgvector** | 0.6+ | 向量存储 | 嵌入检索、RAG |
| **Redis** | 7.x | 缓存/队列 | Cluster模式 |
| **MinIO** | latest | 对象存储 | S3兼容、本地部署 |

### 2.4 LLM选型

| 模型 | 用途 | Token价格 | 上下文 |
|------|------|----------|--------|
| **DeepSeek-V3** | 通用任务 | ¥0.001/1K | 64K |
| **DeepSeek-R1** | 复杂推理 | ¥0.004/1K | 64K |

**选择DeepSeek的原因:**
1. 性价比高（对比GPT-4约1/50价格）
2. 中文理解能力强
3. 支持长上下文
4. API兼容OpenAI格式

## 3. 模块划分

### 3.1 后端模块结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI应用入口
│   ├── config.py               # 配置管理
│   ├── dependencies.py         # 依赖注入
│   │
│   ├── api/                    # API路由
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # 认证接口
│   │   │   ├── users.py        # 用户管理
│   │   │   ├── projects.py     # 项目管理
│   │   │   ├── documents.py    # 文档处理
│   │   │   ├── opportunities.py # 招标机会
│   │   │   ├── generation.py   # 标书生成
│   │   │   └── credits.py      # 积分管理
│   │   └── deps.py             # 路由依赖
│   │
│   ├── core/                   # 核心模块
│   │   ├── __init__.py
│   │   ├── security.py         # 安全/加密
│   │   ├── auth.py             # JWT认证
│   │   └── permissions.py      # 权限控制
│   │
│   ├── models/                 # SQLAlchemy模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── document.py
│   │   ├── opportunity.py
│   │   └── credit.py
│   │
│   ├── schemas/                # Pydantic模式
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── project.py
│   │   └── ...
│   │
│   ├── services/               # 业务逻辑
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── project_service.py
│   │   ├── document_service.py
│   │   └── credit_service.py
│   │
│   ├── agents/                 # AI Agent模块
│   │   ├── __init__.py
│   │   ├── workflows/          # LangGraph工作流
│   │   │   ├── __init__.py
│   │   │   ├── bid_analysis.py
│   │   │   ├── document_gen.py
│   │   │   └── qa_agent.py
│   │   ├── tools/              # Agent工具
│   │   │   ├── __init__.py
│   │   │   ├── search_tool.py
│   │   │   ├── document_tool.py
│   │   │   └── web_tool.py
│   │   ├── prompts/            # Prompt模板
│   │   │   ├── __init__.py
│   │   │   ├── analysis.py
│   │   │   └── generation.py
│   │   └── llm_client.py       # LLM客户端封装
│   │
│   ├── crawler/                # 爬虫模块
│   │   ├── __init__.py
│   │   ├── adb_crawler.py      # ADB爬虫
│   │   ├── parsers/            # 页面解析器
│   │   └── scheduler.py        # 调度器
│   │
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       ├── pdf_parser.py
│       ├── embedding.py
│       └── validators.py
│
├── alembic/                    # 数据库迁移
├── tests/                      # 测试
├── requirements.txt
├── requirements-dev.txt
└── pyproject.toml
```

### 3.2 前端模块结构

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/             # 认证路由组
│   │   │   ├── login/
│   │   │   ├── register/
│   │   │   └── layout.tsx
│   │   ├── (main)/             # 主应用路由组
│   │   │   ├── dashboard/
│   │   │   ├── projects/
│   │   │   │   ├── [id]/
│   │   │   │   └── new/
│   │   │   ├── opportunities/
│   │   │   ├── documents/
│   │   │   └── settings/
│   │   ├── api/                # API Routes (BFF)
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   │
│   ├── components/             # React组件
│   │   ├── ui/                 # shadcn/ui组件
│   │   ├── layout/             # 布局组件
│   │   ├── forms/              # 表单组件
│   │   ├── tables/             # 表格组件
│   │   └── features/           # 功能组件
│   │
│   ├── lib/                    # 工具库
│   │   ├── api/                # API客户端
│   │   ├── utils/              # 工具函数
│   │   └── validations/        # 验证规则
│   │
│   ├── hooks/                  # 自定义Hooks
│   ├── stores/                 # Zustand状态
│   ├── types/                  # TypeScript类型
│   └── messages/               # i18n翻译文件
│       ├── en.json
│       └── zh.json
│
├── public/                     # 静态资源
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

## 4. 部署架构

### 4.1 MVP阶段 (单机部署)

```
┌─────────────────────────────────────────┐
│            云服务器 (4C8G)               │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │           Docker Compose         │   │
│  │                                  │   │
│  │  ┌──────────┐  ┌──────────┐    │   │
│  │  │  Nginx   │  │ Next.js  │    │   │
│  │  │  :80/443 │  │  :3000   │    │   │
│  │  └──────────┘  └──────────┘    │   │
│  │                                  │   │
│  │  ┌──────────┐  ┌──────────┐    │   │
│  │  │ FastAPI  │  │ Celery   │    │   │
│  │  │  :8000   │  │ Worker   │    │   │
│  │  └──────────┘  └──────────┘    │   │
│  │                                  │   │
│  │  ┌──────────┐  ┌──────────┐    │   │
│  │  │PostgreSQL│  │  Redis   │    │   │
│  │  │  :5432   │  │  :6379   │    │   │
│  │  └──────────┘  └──────────┘    │   │
│  │                                  │   │
│  │  ┌──────────┐                   │   │
│  │  │  MinIO   │                   │   │
│  │  │  :9000   │                   │   │
│  │  └──────────┘                   │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### 4.2 docker-compose.yml 示例

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend

  frontend:
    build: ./frontend
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend

  backend:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/bidagent
      - REDIS_URL=redis://redis:6379
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    depends_on:
      - postgres
      - redis

  celery:
    build: ./backend
    command: celery -A app.celery worker -l info
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/bidagent
      - REDIS_URL=redis://redis:6379
    depends_on:
      - backend
      - redis

  postgres:
    image: pgvector/pgvector:pg16
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=bidagent

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

### 4.3 WSL2 开发部署注意事项

> 本项目使用 WSL2/Ubuntu 作为开发环境，配合 Docker Desktop WSL2 集成。

#### 端口映射

WSL2 使用 NAT 网络模式，服务会自动映射到 Windows localhost：
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- MinIO: `localhost:9000` (API), `localhost:9001` (Console)
- 后端 API: `localhost:8000`
- 前端开发服务器: `localhost:3000`

#### 数据卷位置

Docker volumes 在 WSL2 中的存储位置：
```bash
# 命名卷存储位置
/var/lib/docker/volumes/

# 查看卷列表
docker volume ls

# 查看卷详情
docker volume inspect bidagent_postgres_data
```

#### 文件系统性能优化

- ✅ **推荐**: 将项目放在 WSL 原生文件系统 (`~/projects/bid_agent`)
- ⚠️ **避免**: 放在 `/mnt/c/` 或 `/mnt/d/` 下 (I/O 性能显著降低)
- 💡 **提示**: 使用命名卷而非绑定挂载可获得更好的数据库性能

#### 从 Windows 访问 WSL 文件

```bash
# 在 Windows 资源管理器中访问 WSL 文件系统
\\wsl$\Ubuntu\home\<username>\projects\bid_agent
```

## 5. 安全架构

### 5.1 认证流程

```
┌────────┐     ┌────────┐     ┌────────┐     ┌────────┐
│ Client │────▶│ Nginx  │────▶│FastAPI │────▶│  DB    │
└────────┘     └────────┘     └────────┘     └────────┘
     │              │              │
     │   1. Login   │              │
     │─────────────▶│─────────────▶│ 验证凭证
     │              │              │
     │   2. JWT     │              │
     │◀─────────────│◀─────────────│ 生成Token
     │              │              │
     │  3. Request  │              │
     │  + JWT       │              │
     │─────────────▶│─────────────▶│ 验证Token
     │              │              │ 检查权限
     │  4. Response │              │
     │◀─────────────│◀─────────────│
```

### 5.2 安全措施

| 层级 | 措施 |
|------|------|
| **网络层** | Cloudflare WAF, DDoS防护, HTTPS强制 |
| **应用层** | JWT认证, RBAC权限, 请求限流, CSRF防护 |
| **数据层** | 密码bcrypt加密, 敏感数据AES加密, SQL参数化 |
| **审计** | 操作日志, 异常告警, 访问监控 |

## 6. 性能优化

### 6.1 缓存策略

| 数据类型 | 缓存位置 | TTL | 更新策略 |
|---------|---------|-----|---------|
| 用户会话 | Redis | 24h | 登出失效 |
| 机会列表 | Redis | 1h | 爬虫更新后失效 |
| LLM响应 | Redis | 7d | 相同输入命中 |
| 静态资源 | CDN | 30d | 版本hash |

### 6.2 数据库优化

```sql
-- 关键索引
CREATE INDEX idx_opportunities_status_created ON bid_opportunities(status, created_at DESC);
CREATE INDEX idx_documents_project_type ON documents(project_id, doc_type);
CREATE INDEX idx_embeddings_cosine ON embeddings USING ivfflat (vector vector_cosine_ops);

-- 分区表 (积分交易)
CREATE TABLE credit_transactions (
    id BIGSERIAL,
    user_id UUID,
    amount INTEGER,
    created_at TIMESTAMP
) PARTITION BY RANGE (created_at);
```

## 7. 监控告警

### 7.1 监控指标

| 类型 | 指标 | 告警阈值 |
|------|------|---------|
| **系统** | CPU使用率 | > 80% |
| **系统** | 内存使用率 | > 85% |
| **应用** | API响应时间 | > 2s (P99) |
| **应用** | 错误率 | > 1% |
| **业务** | LLM调用失败率 | > 5% |
| **业务** | 积分消费异常 | 单次 > 1000 |

### 7.2 日志规范

```python
# 结构化日志格式
{
    "timestamp": "2026-01-13T10:30:00Z",
    "level": "INFO",
    "service": "bid-agent",
    "trace_id": "abc123",
    "user_id": "user-uuid",
    "action": "generate_bid",
    "duration_ms": 1500,
    "tokens_used": 2000,
    "credits_consumed": 10
}
```

## 8. 扩展性设计

### 8.1 多机构扩展

```python
# 抽象爬虫接口
class BaseCrawler(ABC):
    @abstractmethod
    async def fetch_opportunities(self) -> List[Opportunity]:
        pass
    
    @abstractmethod
    async def fetch_document(self, url: str) -> Document:
        pass

# 具体实现
class ADBCrawler(BaseCrawler):
    ...

class WorldBankCrawler(BaseCrawler):  # 后期扩展
    ...
```

### 8.2 多语言扩展

```
messages/
├── en.json      # 英文
├── zh.json      # 中文
└── fr.json      # 法语 (后期)
```

---

## 相关文档
- [数据模型](./data-model.md)
- [Agent工作流](./agent-workflow.md)
- [API契约](../api-contracts/openapi.yaml)
