# BidAgent V2 — 全栈实施方案

> 版本: 1.0.0 | 日期: 2026-02-11 | 状态: Approved

---

## 1. 实施概述

### 1.1 项目现状

- V1 代码已完全清理，工作区仅保留 `docs/v2/` (7 份设计文档) + 配置文件
- V2 从零搭建，前后端均无任何源代码
- 7 份设计文档已完成：PRD → 架构 → 数据模型 → API → Agent 工作流 → 前端设计 → 开发规范

### 1.2 实施策略

| 维度 | 决策 |
|------|------|
| 开发顺序 | **后端优先** — 先完成 API + DB，再做前端 |
| 迭代节奏 | **按功能里程碑交付**，每个里程碑有明确的 DoD 和验证步骤 |
| P0 范围调整 | MCP Tools + 核心 Skills **纳入 P0** (分析/指导功能依赖它们)；投标计划做 P0 简化版 |
| 文档一致性 | 实施前先修正 6 处文档不一致，确保唯一设计源 |

### 1.3 实施规模

| 维度 | 数量 |
|------|------|
| 数据库表 | ~34 |
| 枚举类型 | 14 |
| 向量索引 | 6 (HNSW) |
| API 端点 | 97 |
| 后端路由文件 | 12 |
| Service 类 | 12+ |
| Agent Skills | 11 |
| MCP Tools | 3 (+1 future) |
| LangGraph 工作流节点 | 8 |
| Prompt 模板 | 16 |
| 前端路由 | 16 |
| React 组件 | ~42 自定义 + 15 shadcn/ui |
| Zustand Stores | 3 |
| API Service 文件 | 12 |
| React Hooks | 7 |
| TypeScript 类型文件 | 6 |
| 爬虫 | 3 (ADB / WB / UNGM) |
| 环境变量 | 30+ |
| 翻译 locale | 2 (zh / en) |

---

## 2. 项目开发标准

> 在任何编码开始前建立，所有里程碑必须遵守。

### 2.1 分支策略

```
main (保护分支, 仅通过 PR 合入)
 └── develop (集成分支)
      ├── feature/<scope>/<desc>   # 功能分支
      ├── fix/<scope>/<desc>       # 修复分支
      └── refactor/<scope>/<desc>  # 重构分支
```

**提交格式**: `<type>(<scope>): <description>`

| type | 用途 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(auth): add JWT login` |
| `fix` | 缺陷修复 | `fix(crawler): handle ADB timeout` |
| `docs` | 文档 | `docs(api): update openapi spec` |
| `refactor` | 重构 | `refactor(services): extract base service` |
| `test` | 测试 | `test(auth): add register validation test` |
| `chore` | 构建/配置 | `chore(deps): upgrade fastapi to 0.115` |
| `perf` | 性能 | `perf(search): add HNSW index` |

**Scope**: `auth`, `crawler`, `credits`, `api`, `agent`, `frontend`, `db`, `deps`, `ci`, `docs`

### 2.2 代码质量门禁

| 检查项 | 后端 (Python) | 前端 (TypeScript) |
|--------|---------------|-------------------|
| Lint | `ruff check .` 零错误 | `npm run lint` 零错误 |
| Format | `ruff format --check .` 通过 | Prettier 格式一致 |
| Build | — | `npm run build` 通过 |
| Tests | `pytest -v` 全部通过 | `npx playwright test` 通过 |
| Coverage | ≥80% (核心 services ≥90%) | — |
| Types | 全部函数有类型提示 | 禁止 `any`，strict mode |
| i18n | — | 所有 UI 文本走 `next-intl` |

### 2.3 文件命名规范

| 语言 | 文件名 | 函数/方法 | 类名 | 常量 |
|------|--------|----------|------|------|
| Python | `snake_case.py` | `snake_case()` | `PascalCase` | `UPPER_SNAKE_CASE` |
| TypeScript | `kebab-case.tsx` | `camelCase()` | `PascalCase` | `UPPER_SNAKE_CASE` |
| SQL | `snake_case` (表/列) | — | — | — |

### 2.4 依赖层级铁律

```
┌───────────┐
│  api/v1/  │ ─────► services/ ─────► models/ + agents/
└───────────┘           │                  │
      ↑                 ↓                  ↓
  schemas/         database.py        llm_client.py
      ↑                                   │
   core/           (基础层)            skills/ → mcp/tools/
```

**规则**:
- `api/` **禁止**直接访问 `models/`，必须经 `services/`
- `services/` **禁止**导入 `api/`
- `core/` 为基础层，**不依赖**任何业务层
- `agents/` 可调用 `services/`，反向禁止

### 2.5 数据库规范

- 主键: UUID v4 (`uuid_generate_v4()`)
- 时间: `TIMESTAMPTZ`，代码中使用 `datetime.now(UTC)`
- 枚举: PostgreSQL 原生 ENUM
- 向量: 1024 维，HNSW 索引 (`m=16, ef_construction=64, cosine`)
- 迁移: Alembic 版本化，V2 首个迁移包含完整 DDL
- 文件哈希: SHA256 (统一标准)

### 2.6 每个里程碑的交付定义 (Definition of Done)

- [ ] 代码通过 lint + 格式检查
- [ ] 单元/集成测试通过 (后端覆盖率 ≥80%)
- [ ] API 有 OpenAPI 文档 (FastAPI 自动生成)
- [ ] 数据库有 Alembic 迁移文件
- [ ] 新增环境变量记录在 `.env.example`
- [ ] `docker compose up` 能一键启动验证
- [ ] 提交格式符合规范

---

## 3. 文档修正 (实施前置任务)

> 在 M0 动工前必须完成，确保唯一设计源。

| # | 问题 | 修正方案 | 影响文件 |
|---|------|---------|---------|
| 1 | `bid_documents.file_hash` — PRD 说 SHA256，数据模型说 MD5 | 统一为 **SHA256** (更安全) | `03-data-model.md` |
| 2 | 项目状态枚举 — PRD: `guiding`，数据模型: `generating` | 统一为 `draft, analyzing, guiding, review, submitted, won, lost` | `03-data-model.md` |
| 3 | 表数量标题写 36 张，实际列出约 34 张 | 盘点后更新标题为实际数量 | `03-data-model.md` |
| 4 | 向量索引 — 架构文档 §5.2 提到 IVFFlat | 统一为 **HNSW** (性能更优) | `02-architecture.md` |
| 5 | MCP/Skills/投标计划的 P0/P1 归属矛盾 | 核心 Skills + MCP Tools 标记为 P0；投标计划标记为 P0-简化版 | `01-prd.md` |
| 6 | RefreshToken 持久化策略缺失 | 补充: refresh_token 存 Redis (7d TTL)，黑名单用 Redis SET | `02-architecture.md`, `04-openapi.md` |

---

## 4. 里程碑详细计划

### M0: 项目脚手架 + 基础设施

> **目标**: 两端项目能启动，数据库能连接，CI 能跑通

#### 后端任务

| # | 任务 | 产出文件 | 说明 |
|---|------|---------|------|
| 1 | 初始化项目结构 | `backend/app/` 全部子目录 + `__init__.py` | 按 `02-architecture.md` 目录结构 |
| 2 | 配置层 | `app/config.py` | Pydantic `BaseSettings`，30+ 环境变量 |
| 3 | 数据库层 | `app/database.py` | `create_async_engine` + `async_sessionmaker` + `get_db` 依赖 |
| 4 | ORM 基类 | `app/models/__init__.py` | `BaseModel(id: UUID, created_at, updated_at)` |
| 5 | 异常体系 | `app/core/exceptions.py` | 7 种异常类 + FastAPI exception_handler |
| 6 | 应用入口 | `app/main.py` | lifespan: validate_config → validate_database → validate_redis |
| 7 | 健康检查 | `app/api/v1/health.py` | `GET /health` (DB + Redis 连通性) |
| 8 | Alembic 初始化 | `alembic/` + `alembic.ini` | async 配置 |
| 9 | Docker Compose | `docker-compose.yml` | pgvector:pg16 + redis:7-alpine + backend + celery-worker |
| 10 | 依赖锁定 | `requirements.txt` | 全部依赖锁版本 |
| 11 | 测试基础 | `pytest.ini` + `tests/conftest.py` | db_session / client / auth_headers fixtures |
| 12 | Lint 配置 | `pyproject.toml` | Ruff: line-length=88, target-version="py312" |

#### 前端任务

| # | 任务 | 产出 | 说明 |
|---|------|------|------|
| 1 | 项目初始化 | `frontend/` 完整目录 | `create-next-app` — Next.js 15 + TS + Tailwind + App Router |
| 2 | UI 组件库 | `components/ui/` (15 个) | `npx shadcn-ui@latest init` |
| 3 | 国际化配置 | `middleware.ts` + `i18n/` | next-intl: config + request + messages 骨架 (zh/en) |
| 4 | Provider | `providers.tsx` | QueryClientProvider |
| 5 | API 客户端 | `services/api-client.ts` | axios 实例 + JWT 拦截器 + credits 头解析 |
| 6 | Lint/Format | `eslint.config.mjs` + `.prettierrc` | ESLint + Prettier |
| 7 | TS 配置 | `tsconfig.json` | strict mode + `@/` 路径别名 |

#### 基础设施

| # | 任务 | 产出 |
|---|------|------|
| 1 | 环境变量模板 | `.env.example` (全量) |
| 2 | Git 忽略 | `.gitignore` (完善) |
| 3 | 编辑器配置 | `.editorconfig` |

#### M0 验证标准

```bash
# 后端
docker compose up -d postgres redis
cd backend && uvicorn app.main:app --reload
curl http://localhost:8000/health  # → 200
cd backend && ruff check .         # → 零错误
cd backend && pytest -v            # → 通过

# 前端
cd frontend && npm run dev
curl http://localhost:3000          # → 页面加载
cd frontend && npm run build       # → 通过
cd frontend && npm run lint        # → 通过
```

---

### M1: 用户系统 + 认证

> **目标**: 注册、登录、JWT 认证链路跑通

#### 后端任务

| # | 任务 | 产出文件 | 关键内容 |
|---|------|---------|---------|
| 1 | User 模型 | `models/user.py` | users 表: email, password_hash, name, company, avatar_url, role(ENUM), language, credits_balance |
| 2 | 请求/响应 Schema | `schemas/user.py` | RegisterRequest, LoginRequest, UserResponse, TokenResponse, RefreshRequest |
| 3 | 安全模块 | `core/security.py` | bcrypt hash/verify, JWT create/decode (HS256, 30min), refresh_token → Redis (7d TTL), `get_current_user` 依赖 |
| 4 | 中间件 | `core/middleware.py` | CORS 白名单 + Redis 滑动窗口速率限制 + 请求日志 |
| 5 | 用户 Service | `services/user_service.py` | register / login / refresh / get_by_id / update_profile |
| 6 | Auth 路由 | `api/v1/auth.py` | 6 个端点: register, login, refresh, logout, me, update-profile |
| 7 | 路由注册 | `api/v1/__init__.py` | APIRouter 挂载入口 |
| 8 | 数据库迁移 | `alembic/versions/001_users_and_auth.py` | users 表 + user_role ENUM |

#### 前端任务

| # | 任务 | 产出文件 |
|---|------|---------|
| 1 | Auth 类型 | `types/auth.ts` |
| 2 | Auth 服务 | `services/auth.ts` |
| 3 | Auth Store | `stores/auth.ts` (Zustand) |
| 4 | Auth Hook | `hooks/use-auth.ts` |
| 5 | Auth Provider | `components/providers/AuthProvider.tsx` (AuthGuard) |
| 6 | 登录页 | `app/[locale]/auth/login/page.tsx` |
| 7 | 注册页 | `app/[locale]/auth/register/page.tsx` |
| 8 | Header 组件 | `components/layout/Header.tsx` (导航 + 用户菜单 + 语言切换) |
| 9 | MainLayout | `components/layout/MainLayout.tsx` (AuthGuard + Header + Footer) |

#### M1 验证标准

```bash
# 注册
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!","name":"测试用户"}'
# → 201, 返回 {user, access_token, refresh_token}

# 登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d '{"email":"test@example.com","password":"Test1234!"}'
# → 200, 返回 token

# 受保护访问
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/auth/me
# → 200, 返回用户信息

# Token 刷新
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -d '{"refresh_token":"<refresh_token>"}'
# → 200, 返回新 token

# 过期/无效 token
curl -H "Authorization: Bearer invalid" http://localhost:8000/api/v1/auth/me
# → 401
```

---

### M2: 招标爬虫 + 浏览 + 项目管理

> **目标**: 三源爬取入库，用户能搜索浏览招标信息并创建项目

#### 后端任务

| # | 任务 | 产出文件 | 关键内容 |
|---|------|---------|---------|
| 1 | Opportunity 模型 | `models/opportunity.py` | opportunities 表: source(ENUM), external_id, title, url, project_number, description, country, sector, status(ENUM), deadline, published_date, estimated_value, procurement_type, search_vector(TSVECTOR) + GIN 索引 + 更新触发器 |
| 2 | Project 模型 | `models/project.py` | projects 表: FK→users, FK→opportunities, title, description, institution, country, status(ENUM: draft→analyzing→guiding→review→submitted→won→lost), deadline |
| 3 | Schemas | `schemas/opportunity.py` + `schemas/project.py` | SearchParams, OpportunityResponse, ProjectCreate/Update/Response |
| 4 | 爬虫基类 | `crawlers/base.py` | `BaseCrawler`: fetch_list / fetch_detail / save_to_db / 统一 TenderInfo 模型 |
| 5 | ADB 爬虫 | `crawlers/adb.py` + `crawlers/cloudflare_bypass.py` | DrissionPage 绕 Cloudflare，ADB 分类映射 |
| 6 | WB 爬虫 | `crawlers/wb.py` | httpx + 3s 速率限制 |
| 7 | UNGM 爬虫 | `crawlers/ungm.py` | httpx，14 个 UN 子机构 |
| 8 | Celery 配置 | `tasks/celery.py` | Redis broker + backend |
| 9 | 爬虫任务 | `tasks/crawler_tasks.py` | crawl_all / crawl_source / manual_trigger |
| 10 | Opportunity Service | `services/opportunity_service.py` | search (TSVECTOR全文) / filter / paginate / get_by_id |
| 11 | Project Service | `services/project_service.py` | CRUD + status_flow / list_by_user / save/unsave |
| 12 | 路由 | `api/v1/opportunities.py` (4 端点) + `api/v1/projects.py` (7 端点) | |
| 13 | 迁移 | `002_opportunities_projects.py` | 2 表 + 2 ENUM + TSVECTOR 触发器 |

#### 前端任务

| # | 任务 | 产出文件 |
|---|------|---------|
| 1 | Types | `types/opportunity.ts` + `types/project.ts` |
| 2 | Services | `services/opportunities.ts` + `services/projects.ts` |
| 3 | Hooks | `hooks/use-opportunities.ts` + `hooks/use-projects.ts` |
| 4 | 组件 | `components/opportunities/OppSearchPanel.tsx` + `OppList.tsx` + `OppCard.tsx` |
| 5 | 招标页面 | `opportunities/page.tsx` (列表+搜索) + `opportunities/[id]/page.tsx` (详情) |
| 6 | 项目页面 | `projects/page.tsx` (列表) + `projects/[id]/page.tsx` (详情) |
| 7 | 仪表板 | `dashboard/page.tsx` (最近项目 + 统计概览) |
| 8 | UI Store | `stores/ui.ts` (sidebar state) |

#### M2 验证标准

```bash
# 手动触发爬取
curl -X POST http://localhost:8000/api/v1/opportunities/crawl?source=adb \
  -H "Authorization: Bearer <admin_token>"
# → 200

# 搜索招标
curl "http://localhost:8000/api/v1/opportunities?search=consulting&source=adb&page=1" \
  -H "Authorization: Bearer <token>"
# → 200, 分页结果

# 创建项目
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer <token>" \
  -d '{"title":"ADB Test","opportunity_id":"<uuid>","institution":"adb"}'
# → 201
```

---

### M3: 文档处理 + 向量化 + 知识库

> **目标**: 上传 PDF 后自动解析、分块、向量化存储；知识库可检索

#### 后端任务

| # | 任务 | 产出文件 | 关键内容 |
|---|------|---------|---------|
| 1 | 文档模型 (6 表) | `models/bid_document.py` | bid_documents, bid_document_sections, bid_document_chunks (vector(1024)), project_documents, project_document_chunks (vector(1024)), translation_cache |
| 2 | 知识库模型 (3 表) | `models/knowledge_base.py` | knowledge_bases, knowledge_documents, knowledge_chunks (vector(1024)) |
| 3 | PDF 解析 | `services/document_processing/pdf_parser.py` | PyMuPDF + 扫描件检测 (50 字符/页阈值) |
| 4 | DOCX 解析 | `services/document_processing/docx_parser.py` | python-docx |
| 5 | 标书解析 | `services/document_processing/bid_document_parser.py` | ADB SBD 章节识别 (7 种 Section Type) |
| 6 | 文本分块 | `services/document_processing/chunker.py` | RecursiveCharacterTextSplitter (1000/200/100) |
| 7 | Embedding 接口 | `services/embedding/base.py` | EmbeddingClient 抽象接口 |
| 8 | 混元 Embedding | `services/embedding/hunyuan.py` | 腾讯混元 1024 维, batch=16 |
| 9 | 智谱 Embedding | `services/embedding/zhipu.py` | 智谱 1024 维, batch=64 |
| 10 | 弹性客户端 | `services/embedding/resilient_client.py` | 指数退避 (3次, 1s基础) + 运行时热切换 |
| 11 | 文档处理任务 | `tasks/document_tasks.py` | Celery: upload_and_process (解析→OCR→分块→向量化→存储) |
| 12 | MCP: 文档搜索 | `agents/mcp/tools/bid_document_search.py` | cosine similarity + score_threshold + section_type filter |
| 13 | MCP: 知识库搜索 | `agents/mcp/tools/knowledge_search.py` | institution + kb_type filter |
| 14 | MCP: 招标查询 | `agents/mcp/tools/opportunity_query.py` | TSVECTOR 全文搜索 |
| 15 | MCP Server | `agents/mcp/server.py` | MCP Server 注册 (进程内调用模式) |
| 16 | 文档 Service | `services/bid_document_service.py` | 上传/解析/搜索/问答(RAG) |
| 17 | 知识库 Service | `services/knowledge_base_service.py` | CRUD + 向量管理 |
| 18 | 路由 | `api/v1/bid_documents.py` (14 端点) + `api/v1/knowledge_base.py` (15 端点) | |
| 19 | 迁移 | `003_documents_knowledge.py` | 9 表 + `CREATE EXTENSION vector` + 6 个 HNSW 索引 |
| 20 | 知识库预置数据 | migration seed | ADB/WB 采购准则 + 评标参考 (4 条) |

#### 前端任务

| # | 任务 | 产出文件 |
|---|------|---------|
| 1 | Bid Workspace Store | `stores/bid-workspace.ts` (Zustand) |
| 2 | 文档 Hook | `hooks/use-documents.ts` |
| 3 | 文档 Service | `services/documents.ts` |
| 4 | 上传步骤 | `components/bid/UploadStep.tsx` (拖拽上传 + 实时进度) |
| 5 | 概览步骤 | `components/bid/OverviewStep.tsx` (文档结构 + AI 分析展示) |
| 6 | 工作台骨架 | `projects/[id]/workspace/page.tsx` + `BidProgressNav` + `BidWorkspace` + `BidChatPanel` |

#### M3 验证标准

```bash
# 上传 PDF
curl -X POST http://localhost:8000/api/v1/bid-documents/projects/<id>/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@test.pdf"
# → 201, 返回 document_id

# 查看解析状态 (Celery 异步处理)
curl http://localhost:8000/api/v1/bid-documents/<doc_id> \
  -H "Authorization: Bearer <token>"
# → 200, processing_status: "completed"

# 向量搜索
curl -X POST http://localhost:8000/api/v1/bid-documents/projects/<id>/search \
  -H "Authorization: Bearer <token>" \
  -d '{"query":"qualification requirements","top_k":5}'
# → 200, 返回相关分块 + 相似度分数

# 知识库搜索
curl "http://localhost:8000/api/v1/knowledge-bases?institution=adb" \
  -H "Authorization: Bearer <token>"
# → 200, 返回 ADB 知识库列表
```

---

### M4: AI 分析 + Skills + LangGraph + 编制指导 ⭐ 核心里程碑

> **目标**: 8 步招标分析跑通，问答式编制指导可用

#### 后端任务

| # | 任务 | 产出文件 | 关键内容 |
|---|------|---------|---------|
| 1 | LLM Client | `agents/llm_client.py` | AsyncOpenAI wrapper (chat / chat_stream / extract_json / summarize / generate_with_context), 模型: V3(通用) + R1(推理), Temperature 策略 |
| 2 | Skills 注册表 | `agents/skills/registry.py` | SkillContext, SkillResult, SkillRegistry |
| 3 | AnalyzeQualification | `agents/skills/analyze_qualification.py` | 4 类资质 (法律/财务/技术/经验) + JV + 国内优惠 |
| 4 | EvaluateCriteria | `agents/skills/evaluate_criteria.py` | 评标方法 (QCBS/QBS/FBS/LCS) + 权重 + 及格线 |
| 5 | ExtractDates | `agents/skills/extract_dates.py` | 6 类关键日期 |
| 6 | ExtractSubmission | `agents/skills/extract_submission.py` | 格式/份数/语言/保函/必交清单 |
| 7 | AnalyzeBDS | `agents/skills/analyze_bds.py` | BDS 逐条修改 + 优先级 + 影响 |
| 8 | AnalyzeCommercial | `agents/skills/analyze_commercial.py` | 付款/保函/保修/违约金/保险/争议 |
| 9 | EvaluateMethodology | `agents/skills/evaluate_methodology.py` | 深度评标方法论 |
| 10 | AssessRisk | `agents/skills/assess_risk.py` | 5 维风险 + Bid/No-Bid (依赖步骤 1-6) |
| 11 | SectionGuidance | `agents/skills/section_guidance.py` | 格式要求/内容要点/评分对标/模板参考/常见错误 |
| 12 | ReviewDraft | `agents/skills/review_draft.py` | 草稿 4 维审查 + 评分 |
| 13 | QualityReview | `agents/skills/quality_review.py` | 全文 4 维审查 (full/quick), 胜率预测 |
| 14 | Prompt 模板 (16) | `agents/prompts/` | system_prompts, adb_analysis, wb_analysis, guidance, quality_review + templates/ |
| 15 | 分析管道 | `services/bid_analysis_service.py` | `run_bid_analysis_pipeline()` — 8 步, 增量/force_refresh/缓存 |
| 16 | LangGraph State | `agents/workflows/bid_guidance/state.py` | BidGuidanceState (TypedDict) |
| 17 | LangGraph Graph | `agents/workflows/bid_guidance/graph.py` | 8 节点 + RedisSaver 检查点 |
| 18 | LangGraph Nodes | `agents/workflows/bid_guidance/nodes.py` | intake_documents → analyze_tor → extract_criteria → build_structure → guidance_router ↔ provide_guidance / review_draft → quality_check |
| 19 | RAG 上下文组装 | agents 内部复用 | 多 query 搜索 → 去重 → 限制 15 doc + 5 kb |
| 20 | 分析模型 | `models/bid_analysis.py` | bid_analyses (1:1 projects), bid_predictions |
| 21 | 质量审查 Service | `services/quality_review_service.py` | |
| 22 | 路由 | `api/v1/bid_analysis.py` (2) + `api/v1/quality_review.py` (7) + `api/v1/guidance.py` (7, 含 SSE) | |
| 23 | 迁移 | `004_analysis_guidance.py` | bid_analyses + bid_predictions |

#### 前端任务

| # | 任务 | 产出文件 |
|---|------|---------|
| 1 | 分析步骤组件 | `components/bid/AnalysisStep.tsx` (8 维分析结果展示) |
| 2 | 指导面板 | `components/bid/generation/GenerationPanel.tsx` (Q&A 交互界面) |
| 3 | 审查面板 | `components/bid/quality/QualityReviewPanel.tsx` |
| 4 | 分析 Service | `services/bid-analysis.ts` |
| 5 | 指导 Service | `services/generation.ts` (含 SSE `streamGuidance` AsyncGenerator) |
| 6 | Hooks | `hooks/use-bid-analysis.ts` + `hooks/use-generation.ts` |
| 7 | Types | `types/bid.ts` 扩展 + `types/generation.ts` (完整类型定义) |

#### SSE 流式交互设计

```
用户发送消息 → POST /guidance/ask-stream
                    ↓
事件流:  thinking → chunk × N → reference × N → complete
                    ↓
前端:    AsyncGenerator 消费 → 实时渲染 → invalidate 缓存
```

#### M4 验证标准

```bash
# 触发 8 步分析
curl -X POST http://localhost:8000/api/v1/projects/<id>/analysis/start \
  -H "Authorization: Bearer <token>"
# → 200, 返回分析任务 ID

# 获取分析结果
curl http://localhost:8000/api/v1/projects/<id>/analysis/result \
  -H "Authorization: Bearer <token>"
# → 200, 8 维分析结果

# 编制指导 Q&A (流式)
curl -X POST http://localhost:8000/api/v1/guidance/ask-stream \
  -H "Authorization: Bearer <token>" \
  -H "Accept: text/event-stream" \
  -d '{"project_id":"<uuid>","message":"请指导我写技术方案章节"}'
# → SSE 事件流

# 草稿审查
curl -X POST http://localhost:8000/api/v1/guidance/review-draft \
  -H "Authorization: Bearer <token>" \
  -d '{"project_id":"<uuid>","section_id":"tech_approach","draft_content":"..."}'
# → 200, 4 维审查评分 + 改进建议

# 全文质量审查
curl -X POST http://localhost:8000/api/v1/projects/<id>/quality-review/full \
  -H "Authorization: Bearer <token>"
# → 200, completeness + compliance + consistency + risks + overall_score
```

---

### M5: 投标计划 (简化版) + 积分系统 + 落地页

> **目标**: 工作台 7 步全部可用，积分扣减跑通，落地页上线

#### 后端任务

| # | 任务 | 产出文件 | 关键内容 |
|---|------|---------|---------|
| 1 | 投标计划模型 | `models/bid_plan.py` | bid_plans (1:1 projects) + bid_plan_tasks + 统计触发器 |
| 2 | 支付模型 | `models/payment.py` | payment_orders, payment_transactions, recharge_packages |
| 3 | 投标计划 Service | `services/bid_plan_service.py` | AI 生成待办 + CRUD + 状态更新 |
| 4 | 支付 Service | `services/payment_service.py` | 积分充值 / 扣减 / 查余额 / 交易记录 |
| 5 | 积分扣减中间件 | (集成到 guidance/analysis 路由) | 每个 AI 调用自动扣减 + `X-Credits-Consumed` / `X-Credits-Remaining` 响应头 |
| 6 | 路由 | `api/v1/bid_plan.py` (6 端点) + `api/v1/payment.py` (7 端点) | |
| 7 | 迁移 | `005_plan_payment.py` | 5 表 + 触发器 |

#### 前端任务

| # | 任务 | 产出文件 |
|---|------|---------|
| 1 | 投标计划 | `components/bid/PlanStep.tsx` (任务列表 + 简化时间线) |
| 2 | 进度跟踪 | `components/bid/TrackingStep.tsx` |
| 3 | 积分管理 | `app/[locale]/credits/page.tsx` |
| 4 | 支付弹窗 | `components/payment/PaymentDialog.tsx` |
| 5 | 积分 Service | `services/credits.ts` |
| 6 | 积分 Hook | `hooks/use-credits.ts` |
| 7 | **落地页 (13 组件)** | `components/landing/`: LandingNav, HeroSection, TrustBar, PainPointsSection, FeaturesSection, WorkflowSection, ComparisonSection, PersonasSection, StatsSection, PricingSection, FAQSection, CTASection, LandingFooter |
| 8 | 落地页页面 | `app/[locale]/page.tsx` (Server Component, SEO) |
| 9 | 落地页 i18n | `messages/{zh,en}.json` 中 `landing.*` 全量翻译 |

#### M5 验证标准

- 工作台 7 个步骤全部可进入、功能可用
- 积分扣减: AI 调用后余额减少，headers 正确
- 积分不足: 返回 402 错误
- 落地页: SEO 元数据、11 个 Section 全部渲染、响应式 (lg/md/sm)、动画效果

---

### M6: 统计 + 管理 + 设置 + 打磨

> **目标**: 管理员功能完整，全面测试通过，生产就绪

#### 后端任务

| # | 任务 | 产出文件 |
|---|------|---------|
| 1 | 统计模型 | `models/stats.py` — daily_stats, usage_logs, system_metrics, saved_searches |
| 2 | 统计 Service | `services/stats_service.py` — 运营/用户/财务统计聚合 |
| 3 | 统计路由 | `api/v1/stats.py` (7 端点, Admin only) |
| 4 | 日志规范化 | JSON 结构化日志 (production): timestamp, level, logger, message, project_id, user_id, duration_ms |
| 5 | 性能优化 | DB 连接池调优 + Redis 缓存热点 + 查询优化 + N+1 检测 |
| 6 | 迁移 | `006_stats_operations.py` |

#### 前端任务

| # | 任务 | 产出文件 |
|---|------|---------|
| 1 | 设置页面 (4页) | `settings/profile`, `settings/credits`, `settings/notifications`, `settings/security` |
| 2 | 设置布局 | `components/settings/SettingsLayout.tsx` |
| 3 | 帮助中心 | `app/[locale]/help/page.tsx` |
| 4 | 知识库助手 | `components/knowledge-base/BidAssistant.tsx` + `DashboardAssistantWidget.tsx` |
| 5 | 响应式适配 | 全页面移动端兼容 |
| 6 | i18n 补齐 | 全量中英文翻译 |
| 7 | Footer | `components/layout/Footer.tsx` |

#### M6 最终验证

```bash
# 后端质量
cd backend && ruff check .                     # → 零错误
cd backend && ruff format --check .            # → 格式一致
cd backend && pytest --cov=app --cov-report=xml # → ≥80% 覆盖率
cd backend && pytest tests/services/ --cov=app/services # → ≥90%

# 前端质量
cd frontend && npm run lint                    # → 零错误
cd frontend && npm run build                   # → 通过
cd frontend && npx playwright test             # → 通过

# 全链路测试 (Docker Compose)
docker compose up -d
# 1. 访问落地页 → 注册 → 登录
# 2. 浏览招标 → 搜索 → 创建项目
# 3. 上传 PDF → 自动解析 → 向量化
# 4. 触发 8 步分析 → 查看结果
# 5. Q&A 指导 → 提交草稿 → 审查反馈
# 6. 投标计划 → 任务管理
# 7. 质量审查 → 导出
# 8. 积分消耗 → 充值
```

---

## 5. 里程碑依赖图

```
           修正文档不一致 (6项)
                │
                ▼
    ┌─────────────────────┐
    │  M0: 脚手架+基础设施  │
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │  M1: 用户系统+认证    │
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │  M2: 爬虫+浏览+项目   │
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │  M3: 文档+向量化+KB   │
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │  M4: AI分析+指导 ⭐   │  ← 核心里程碑
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │  M5: 计划+积分+落地页  │
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │  M6: 统计+管理+打磨   │  → 生产就绪
    └─────────────────────┘
```

---

## 6. 技术风险与缓解

| 风险 | 影响级别 | 缓解措施 |
|------|---------|---------|
| DeepSeek API 不稳定 | **高** — AI 功能全线中断 | LLM Client 内置重试 (3 次指数退避) + rule-based fallback 默认结果 |
| 腾讯混元 Embedding 降级 | **中** — 向量化延迟增加 | `ResilientEmbeddingClient` 自动切换智谱 |
| PaddleOCR CPU 模式慢 | **中** — 大 PDF 处理超时 | `asyncio.Semaphore` 限并发 + Celery 异步 + 60s 超时 |
| ADB Cloudflare 反爬升级 | **中** — 爬虫失败 | DrissionPage + 代理池 + 手动触发降级方案 |
| Redis 不可用 | **中** — 工作流/缓存中断 | FastAPI `BackgroundTasks` 降级 + 内存缓存 |
| pgvector HNSW 索引重建慢 | **低** — 数据迁移耗时 | 首次迁移一次性建好，后续仅追加数据 |
| 前端 SSE 连接断开 | **低** — 流式输出中断 | 自动重连 + 断点续传 (message_id 去重) |

---

## 7. 测试策略

### 7.1 测试分类

| 类型 | 工具 | 执行频率 | 覆盖范围 |
|------|------|---------|---------|
| 单元测试 | pytest + pytest-asyncio | 每次提交 | Services, Skills, Utils |
| 集成测试 | pytest + httpx AsyncClient | 每个里程碑 | API 端点 + DB |
| E2E 测试 | Playwright | M5/M6 | 核心用户流程 |
| Lint | Ruff + ESLint | 每次提交 | 全量代码 |
| 类型检查 | mypy (Python) + tsc (TS) | 每次构建 | 全量代码 |
| 性能测试 | 手动 | M6 | 向量搜索 <200ms, API P95 <500ms |

### 7.2 测试目录结构

```
backend/tests/
├── conftest.py           # fixtures: db_session, client, mock_llm, auth_headers
├── api/
│   ├── test_auth.py
│   ├── test_opportunities.py
│   ├── test_projects.py
│   ├── test_bid_documents.py
│   ├── test_bid_analysis.py
│   ├── test_guidance.py
│   ├── test_quality_review.py
│   ├── test_bid_plan.py
│   ├── test_payment.py
│   └── test_knowledge_base.py
├── services/
│   ├── test_user_service.py
│   ├── test_opportunity_service.py
│   ├── test_project_service.py
│   ├── test_bid_document_service.py
│   ├── test_bid_analysis_service.py
│   └── test_payment_service.py
├── agents/
│   ├── test_llm_client.py
│   ├── test_skills.py
│   └── test_workflow.py
├── core/
│   ├── test_security.py
│   └── test_middleware.py
└── crawlers/
    ├── test_adb_crawler.py
    ├── test_wb_crawler.py
    └── test_ungm_crawler.py

frontend/tests/
├── e2e/
│   ├── auth.spec.ts
│   ├── opportunities.spec.ts
│   ├── workspace.spec.ts
│   └── landing.spec.ts
└── playwright.config.ts
```

### 7.3 关键测试用例

| 场景 | 类型 | 验证点 |
|------|------|--------|
| 注册 → 登录 → JWT 鉴权 | 集成 | Token 生成/验证/刷新/过期拒绝 |
| 上传 PDF → 自动解析 → 向量化 | 集成 | Celery 异步处理 + 状态更新 + 向量存储 |
| 向量搜索返回相关结果 | 单元 | cosine similarity 排序 + threshold 过滤 |
| 8 步分析管道完整执行 | 集成 | 增量/缓存/force_refresh 行为 |
| 指导 Q&A 智能路由 | 单元 | 意图识别 → prompt 回答 vs Skills 分析 |
| SSE 流式输出 | 集成 | 事件顺序 + 内容完整 + 错误处理 |
| 积分扣减并发安全 | 单元 | 乐观锁/FOR UPDATE 防止超扣 |
| 爬虫超时/失败恢复 | 单元 | 重试策略 + 部分失败不影响整体 |

---

## 8. 环境变量清单

> 完整列表，按里程碑标注首次需要时机。

```bash
# ===== M0: 基础设施 =====
APP_NAME=bidagent
APP_ENV=development                 # development | staging | production
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://bidagent:password@localhost:5432/bidagent
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30

# Redis
REDIS_URL=redis://localhost:6379/0

# ===== M1: 认证 =====
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

CORS_ORIGINS=http://localhost:3000
RATE_LIMIT_PER_MINUTE=60

# ===== M2: 爬虫 =====
CRAWLER_PROXY_URL=                  # 可选代理
CRAWLER_REQUEST_TIMEOUT=30
CRAWLER_ADB_DELAY=5                 # ADB 请求间隔 (s)
CRAWLER_WB_DELAY=3
CRAWLER_UNGM_DELAY=2

# ===== M3: 文档 + Embedding =====
# 腾讯混元 (主 Embedding)
HUNYUAN_API_KEY=your-hunyuan-key
HUNYUAN_EMBEDDING_MODEL=hunyuan-embedding
HUNYUAN_EMBEDDING_DIM=1024

# 智谱 (降级 Embedding)
ZHIPU_API_KEY=your-zhipu-key
ZHIPU_EMBEDDING_MODEL=embedding-3
ZHIPU_EMBEDDING_DIM=1024

# 文件上传
UPLOAD_DIR=./data/uploads
MAX_UPLOAD_SIZE_MB=50

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# ===== M4: LLM =====
DEEPSEEK_API_KEY=your-deepseek-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL_V3=deepseek-chat
DEEPSEEK_MODEL_R1=deepseek-reasoner
LLM_MAX_RETRIES=3
LLM_RETRY_BASE_DELAY=1.0

# ===== M5: 支付 =====
# (预留，P0 阶段手动充值)
ALIPAY_APP_ID=
ALIPAY_PRIVATE_KEY=
WECHAT_PAY_APP_ID=
WECHAT_PAY_MCH_ID=

# ===== 前端 =====
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_DEFAULT_LOCALE=zh
```

---

## 9. Docker Compose 架构

```yaml
services:
  postgres:       # pgvector/pgvector:pg16, port 5432, healthcheck
  redis:          # redis:7-alpine, port 6379, healthcheck
  backend:        # FastAPI, port 8000, depends_on: postgres + redis
  celery-worker:  # 同 backend 镜像, depends_on: postgres + redis
  frontend:       # Next.js, port 3000, depends_on: backend
```

**数据卷**:
- `postgres_data` — 数据库持久化
- `redis_data` — Redis 持久化
- `upload_data` — 上传文件

---

## 10. 参考文档索引

| 里程碑 | 主要参考文档 |
|--------|-------------|
| M0 | `02-architecture.md` §1-2, `07-dev-standards.md` 全文 |
| M1 | `01-prd.md` §4.1, `03-data-model.md` §users, `04-openapi.md` §3.1 |
| M2 | `01-prd.md` §4.2, `03-data-model.md` §opportunities+projects, `04-openapi.md` §3.2-3.3 |
| M3 | `01-prd.md` §4.3, `03-data-model.md` §documents+knowledge, `04-openapi.md` §3.5-3.6+3.11, `05-agent-workflow.md` §3 |
| M4 | `01-prd.md` §4.4-4.6, `05-agent-workflow.md` 全文, `04-openapi.md` §3.7-3.10 |
| M5 | `01-prd.md` §4.7-4.8, `03-data-model.md` §plans+payments, `06-frontend-design.md` §6.0 |
| M6 | `03-data-model.md` §operations, `04-openapi.md` §3.13, `07-dev-standards.md` §6 |
