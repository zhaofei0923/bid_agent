# BidAgent V2 API 当前实现快照

> 版本: 2.0.0 | 日期: 2026-05-04 | 状态: Current Implementation
> 本文档按当前 `backend/app/api` 注册路由整理，用于开发、测试和验收现有功能。它不是早期接口规划文档，也不声明尚未接入的后续功能。

## 1. 全局约定

### 1.1 基础路径

```yaml
development: http://localhost:8000/v1
production: https://api.bidagent.com/v1
```

所有路径以下文列出的相对路径为准，例如 `GET /projects` 对应完整路径 `GET /v1/projects`。

### 1.2 认证

大多数业务接口使用 JWT Bearer Token。

```http
Authorization: Bearer <access_token>
```

无需登录的接口：

- `GET /health`
- `GET /public/opportunities`
- `GET /public/opportunities/latest`
- `POST /auth/register`
- `POST /auth/verify-email`
- `POST /auth/resend-verification`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/forgot-password`
- `POST /auth/reset-password`

管理员接口依赖 `require_admin`：

- `/admin/*`
- `POST /knowledge-bases/`
- `DELETE /knowledge-bases/{kb_id}`
- `GET /stats/overview`
- `GET /stats/daily`

### 1.3 通用响应

分页响应：

```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

应用异常响应：

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found",
    "detail": null
  }
}
```

常用积分响应头：

| Header | 说明 |
|--------|------|
| `X-Credits-Consumed` | 本次请求预估或实际消耗积分 |
| `X-Credits-Remaining` | 当前剩余积分 |
| `X-Process-Time` | 请求耗时 |

## 2. 当前端点总览

当前 `backend/app/api/v1` 中共有 66 个 route decorator。`app.main` 还保留一个同路径的健康检查，外部使用时按一个 `GET /health` 端点理解即可。

| 模块 | 前缀 | 端点数 | 说明 |
|------|------|--------|------|
| Health | `/health` | 1 | 存活检查 |
| Public | `/public` | 2 | 公开机会检索 |
| Auth | `/auth` | 10 | 注册、邮箱验证、登录、资料、密码 |
| Opportunities | `/opportunities` | 2 | 登录后机会列表和详情 |
| Projects | `/projects` | 5 | 项目 CRUD |
| Bid Documents | `/projects/{project_id}/bid-documents` | 7 | 招标文件上传、解析触发、章节、诊断 |
| Bid Analysis | `/projects/{project_id}/analysis` | 2 | 分析结果与触发 |
| Guidance | `/projects/{project_id}` | 6 | AI 指导、SSE、聊天历史、清单 |
| Knowledge Base | `/knowledge-bases` | 6 | 全局知识库 CRUD 与搜索 |
| Bid Plan | `/projects/{project_id}/plan` | 9 | 投标计划与任务 |
| Quality Review | `/projects/{project_id}/quality-review` | 2 | 全量/快速质量审查 |
| Document Review | `/projects/{project_id}/document-review` | 1 | 单项材料审查 |
| Reading Tips | `/projects/{project_id}/reading-tips` | 1 | 阅读与编制建议 |
| Payment | `/payment` | 4 | 余额、流水、套餐、订单创建 |
| Stats | `/stats` | 3 | 管理统计与个人统计 |
| Admin | `/admin` | 5 | 用户管理和积分调整 |

## 3. 端点详情

### 3.1 Health

#### `GET /health`

- Auth: 无
- Response: `{ "status": "ok", "version": string }`

### 3.2 Public

#### `GET /public/opportunities`

- Auth: 无
- Query: `search?`, `source?`, `country?`, `sector?`, `sort_by?`, `sort_order?`, `page`, `page_size`
- 公开列表限制页数和每页数量，用于未登录浏览。

#### `GET /public/opportunities/latest`

- Auth: 无
- 返回最新公开招标机会。

### 3.3 Auth

#### `POST /auth/register`

- Auth: 无
- Status: 201
- Request: `email`, `password`, `name`, `company?`
- 当前注册流程会创建未验证用户并发送邮箱验证码，不直接返回 token。

#### `POST /auth/verify-email`

- Auth: 无
- Request: `email`, `code`
- Response: `access_token`, `refresh_token`, `token_type`, `expires_in`

#### `POST /auth/resend-verification`

- Auth: 无
- Request: `email`
- 重新发送邮箱验证码，服务端有频率限制。

#### `POST /auth/login`

- Auth: 无
- Request: `email`, `password`
- Response: `TokenResponse`

#### `POST /auth/refresh`

- Auth: 无
- Request: `refresh_token`
- Response: `TokenResponse`

#### `GET /auth/me`

- Auth: JWT
- Response: `UserResponse`

#### `PUT /auth/me`

- Auth: JWT
- Request: `UserUpdate`
- Response: `UserResponse`

#### `PUT /auth/password`

- Auth: JWT
- Request: `current_password`, `new_password`
- Response: `{ "message": string }`

#### `POST /auth/forgot-password`

- Auth: 无
- Request: `email`
- Response: generic success message, avoids account enumeration.

#### `POST /auth/reset-password`

- Auth: 无
- Request: `token`, `new_password`
- Response: `{ "message": string }`

### 3.4 Opportunities

#### `GET /opportunities`

- Auth: JWT
- Query:
  - `search?: string`
  - `source?: "adb" | "wb" | "afdb"`
  - `status?: "open" | "closed" | "cancelled" | "all"`
  - `country?: string`
  - `sector?: string`
  - `sort_by?: "published_at" | "deadline" | "created_at" | "updated_at" | "title" | "source" | "country" | "sector"`
  - `sort_order?: "asc" | "desc"`
  - `page: integer >= 1`
  - `page_size: integer 1-100`
- Response: `PaginatedOpportunities`

#### `GET /opportunities/{opportunity_id}`

- Auth: JWT
- Response: `OpportunityResponse`

### 3.5 Projects

#### `POST /projects`

- Auth: JWT
- Status: 201
- Request: `ProjectCreate`
- Response: `ProjectResponse`

#### `GET /projects`

- Auth: JWT
- Query: `page`, `page_size`
- 仅返回当前用户项目。

#### `GET /projects/{project_id}`

- Auth: JWT, owner only
- Response: `ProjectResponse`

#### `PUT /projects/{project_id}`

- Auth: JWT, owner only
- Request: `ProjectUpdate`
- Response: `ProjectResponse`

#### `DELETE /projects/{project_id}`

- Auth: JWT, owner only
- Status: 204

### 3.6 Bid Documents

#### `POST /projects/{project_id}/bid-documents`

- Auth: JWT, project owner
- Content-Type: `multipart/form-data`
- FormData: `file`
- 支持 PDF/DOCX。服务端会校验扩展名、MIME、文件魔数、大小、重复 hash，并使用安全唯一文件名保存。
- 上传成功后尝试派发 Celery `process_document` 任务。

#### `GET /projects/{project_id}/bid-documents`

- Auth: JWT, project owner
- Response: `BidDocumentResponse[]`

#### `POST /projects/{project_id}/bid-documents/analyze-combined`

- Auth: JWT, project owner
- Status: 202
- 触发项目内所有已处理招标文件的合并 AI 概览任务。

#### `DELETE /projects/{project_id}/bid-documents/{document_id}`

- Auth: JWT, project owner
- Status: 204
- 删除文档记录和磁盘文件，文档必须属于该项目。

#### `POST /projects/{project_id}/bid-documents/{document_id}/analyze`

- Auth: JWT, project owner
- Status: 202
- 触发单个文档的 AI 概览和阅读提示生成任务。

#### `GET /projects/{project_id}/bid-documents/{document_id}/sections`

- Auth: JWT, project owner
- Response: `BidDocumentSectionResponse[]`

#### `GET /projects/{project_id}/bid-documents/diagnostics`

- Auth: JWT, project owner
- 返回项目文档 chunk 数、向量覆盖率、section type 分布等诊断信息。

### 3.7 Bid Analysis

#### `GET /projects/{project_id}/analysis`

- Auth: JWT, project owner
- Response: `BidAnalysis`

#### `POST /projects/{project_id}/analysis/trigger`

- Auth: JWT, project owner
- Query: `steps?: string[]`, `force_refresh?: boolean`
- Credits: `bid_analysis_trigger`
- 同步执行当前 8 步分析 pipeline，成功后扣积分。

### 3.8 Guidance

#### `POST /projects/{project_id}/guidance`

- Auth: JWT, project owner
- Request: `GuidanceRequest`
- Credits: `guidance_qa`
- 非流式 AI 编制指导，成功后扣积分。

#### `POST /projects/{project_id}/guidance/stream`

- Auth: JWT, project owner
- Request: `GuidanceRequest`
- Response: `text/event-stream`
- Credits: `guidance_stream`
- 流式输出 AI 指导内容，完成后发送积分事件并扣费。

#### `GET /projects/{project_id}/guidance/history`

- Auth: JWT, project owner
- 返回当前用户和项目的 Redis 会话历史。

#### `DELETE /projects/{project_id}/guidance/history`

- Auth: JWT, project owner
- 清空当前用户和项目的 Redis 会话历史。

#### `POST /projects/{project_id}/checklist/generate`

- Auth: JWT, project owner
- 生成投标文件提交清单。

#### `POST /projects/{project_id}/checklist/translate`

- Auth: JWT, project owner
- 翻译提交清单。

### 3.9 Knowledge Base

#### `POST /knowledge-bases/`

- Auth: JWT + Admin
- Status: 201
- Request: `name`, `description?`, `institution`, `kb_type`
- 创建全局知识库。

#### `GET /knowledge-bases/`

- Auth: JWT
- Query: `institution?: "adb" | "wb" | "afdb"`, `kb_type?: "guide" | "review" | "template"`
- Response: `KnowledgeBaseResponse[]`

#### `GET /knowledge-bases/{kb_id}`

- Auth: JWT
- Response: `KnowledgeBaseResponse`

#### `DELETE /knowledge-bases/{kb_id}`

- Auth: JWT + Admin
- Status: 204

#### `POST /knowledge-bases/search`

- Auth: JWT
- Request: `query`, `institution?`, `kb_type?`, `top_k?`, `score_threshold?`
- Response: `KnowledgeSearchResult[]`

#### `POST /knowledge-bases/{kb_id}/search`

- Auth: JWT
- Request: `query`, `top_k?`, `score_threshold?`
- 在指定知识库维度内搜索。

### 3.10 Bid Plan

#### `GET /projects/{project_id}/plan`

- Auth: JWT, project owner
- 返回项目投标计划。

#### `POST /projects/{project_id}/plan`

- Auth: JWT, project owner
- Request: `title?`, `name?`, `description?`
- 创建或更新项目投标计划。

#### `GET /projects/{project_id}/plan/tasks`

- Auth: JWT, project owner
- 返回计划任务列表。

#### `POST /projects/{project_id}/plan/tasks`

- Auth: JWT, project owner
- Request: `title`, `description?`, `category?`, `priority?`, `assignee?`, `assigned_to?`, `start_date?`, `due_date?`, `notes?`, `sort_order?`, `status?`
- 添加任务。`assigned_to` 会兼容映射到后端字段 `assignee`。

#### `PATCH /projects/{project_id}/plan/tasks/{task_id}`

- Auth: JWT, project owner
- Request: task partial fields
- 任务必须属于该项目的 plan。

#### `PUT /projects/{project_id}/plan/tasks/{task_id}/status`

- Auth: JWT, project owner
- Query: `status`
- 更新任务状态。

#### `DELETE /projects/{project_id}/plan/tasks/{task_id}`

- Auth: JWT, project owner
- 删除任务，任务必须属于该项目的 plan。

#### `POST /projects/{project_id}/plan/reorder`

- Auth: JWT, project owner
- Request: `task_ids: uuid[]`
- 按传入顺序更新任务排序。

#### `POST /projects/{project_id}/plan/generate`

- Auth: JWT, project owner
- 基于项目上下文生成投标准备任务。

### 3.11 Quality Review

#### `POST /projects/{project_id}/quality-review/full`

- Auth: JWT, project owner
- Request: `proposal_content`
- Credits: `quality_review_full`
- 运行完整质量审查，成功后扣积分。

#### `POST /projects/{project_id}/quality-review/quick`

- Auth: JWT, project owner
- Request: `proposal_content`
- Credits: `quality_review_quick`
- 运行快速质量审查，成功后扣积分。

### 3.12 Document Review

#### `POST /projects/{project_id}/document-review/item`

- Auth: JWT, project owner
- Content-Type: `multipart/form-data`
- FormData: `item_title`, `item_guidance?`, `source_section?`, `source_excerpt?`, `content_text?`, `file?`
- 支持粘贴文本或上传 PDF/JPG/PNG/WEBP，文件上限 10MB。
- Credits: `doc_review_item`

### 3.13 Reading Tips

#### `POST /projects/{project_id}/reading-tips`

- Auth: JWT, project owner
- Credits: `guidance_qa`
- 基于项目合并概览和知识库 RAG 生成招标文件阅读建议与投标编制建议。

### 3.14 Payment

#### `GET /payment/balance`

- Auth: JWT
- Response: `{ "balance": number }`

#### `GET /payment/transactions`

- Auth: JWT
- Query: `page`, `page_size`
- 返回当前用户积分流水。

#### `GET /payment/packages`

- Auth: 无强制登录依赖
- Response: `PackageResponse[]`

#### `POST /payment/orders`

- Auth: JWT
- Request: `package_id`, `payment_method: "alipay" | "wechat" | "bank_transfer"`
- 创建待支付订单。当前实现只创建订单记录，不包含第三方支付回调、退款或自动入账闭环。

普通用户不能通过公开接口直接给自己加积分或扣积分。手动积分调整通过管理员接口完成。

### 3.15 Stats

#### `GET /stats/overview`

- Auth: JWT + Admin
- 返回平台用户、项目、机会、分析数量及当日活跃用户等概览。

#### `GET /stats/daily`

- Auth: JWT + Admin
- Query: `start_date`, `end_date`
- 返回日期范围内的 `DailyStats` 聚合。

#### `GET /stats/users/me`

- Auth: JWT
- 返回当前用户项目数、分析数、积分消耗、最近活跃时间。

### 3.16 Admin

#### `GET /admin/users`

- Auth: JWT + Admin
- Query: `search?`, `page`, `page_size`
- 返回用户分页列表。

#### `GET /admin/users/{user_id}`

- Auth: JWT + Admin
- 返回用户详情。

#### `POST /admin/users/{user_id}/credits/adjust`

- Auth: JWT + Admin
- Request: `amount`, `reason`
- 正数增加积分，负数扣减积分。服务端使用行锁更新余额并记录流水。

#### `GET /admin/users/{user_id}/transactions`

- Auth: JWT + Admin
- Query: `page`, `page_size`
- 返回指定用户积分流水。

#### `PUT /admin/users/{user_id}/role`

- Auth: JWT + Admin
- Request: `role`
- 修改用户角色，不能修改自己的角色。

## 4. 当前未作为 API 合同声明的内容

以下内容存在于早期设计或部分模型/实验代码中，但不是当前实现的 API 合同：

- `/payments/*` 复数支付路径、第三方支付 webhook、退款、自动入账闭环。
- `/projects/{project_id}/prediction` 评标预测接口。
- `/projects/{project_id}/workflow` 工作流接口。
- `/projects/{project_id}/analyze-tor`、`/projects/{project_id}/qa` 项目文档问答接口。
- 知识库文档上传、批量导入、知识库 QA、流程/评审标准专用接口。
- 独立 `/guidance/ask`、`/guidance/section-guidance`、`/guidance/review-draft` 路径；当前指导能力挂载在 `/projects/{project_id}/guidance*`。
- 招标机会管理员创建/更新接口；当前仅支持列表和详情查询。

如后续恢复或新增这些能力，应先实现路由和测试，再把本文件提升为新的合同版本。
