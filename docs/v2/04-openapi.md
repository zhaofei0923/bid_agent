# BidAgent V2 — OpenAPI 接口契约

> 版本: 2.0.0 | 日期: 2026-02-11 | 状态: Draft  
> 完整 YAML 文件将在实现阶段自动生成，此文档作为设计蓝图。

## 1. 全局约定

### 1.1 基础信息

```yaml
openapi: 3.1.0
info:
  title: BidAgent API
  version: 2.0.0
  description: AI-powered bidding platform for multilateral development banks
servers:
  - url: http://localhost:8000/v1
    description: Development
  - url: https://api.bidagent.com/v1
    description: Production
```

### 1.2 认证

```yaml
securityDefinitions:
  BearerAuth:
    type: http
    scheme: bearer
    bearerFormat: JWT
```

所有需认证的端点添加: `security: [{ BearerAuth: [] }]`

### 1.3 通用响应格式

**成功响应**:
```json
{
  "id": "uuid",
  "field": "value"
}
```

**错误响应**:
```json
{
  "code": "NOT_FOUND",
  "message": "Resource not found",
  "detail": null
}
```

**分页响应**:
```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

### 1.4 通用响应头

| Header | 说明 |
|--------|------|
| `X-Credits-Consumed` | 本次请求消耗的积分 |
| `X-Credits-Remaining` | 当前剩余积分 |
| `X-Request-Id` | 请求追踪 ID |

---

## 2. API 端点总览

### V1 → V2 变更

| 变更 | 说明 |
|------|------|
| **全部启用 JWT** | V1 中大量端点未认证，V2 全部强制 JWT (除 register/login/webhook/health) |
| **修复路径双重前缀** | V1 的 payment/stats/generate 模块有 `/v1/xxx/xxx/endpoint` 问题 |
| **统一 UUID 路径参数** | 所有 `{id}` 参数类型为 `UUID` |
| **规范 HTTP 状态码** | 201/204/400/401/403/404/422/429/500/502 |
| **添加速率限制** | 429 + `Retry-After` header |
| **SSE 指导流式** | 替代 V1 的伪流式，使用标准 `text/event-stream` |

---

## 3. 端点详细定义

### 3.1 认证 (`/auth`)

#### `POST /auth/register` — 用户注册

- Auth: 无
- Status: 201

```yaml
Request:
  email: string (email format, required)
  password: string (min: 8, required)
  name: string (1-100, required)
  company: string (optional)

Response 201:
  id: uuid
  email: string
  name: string
  company: string?
  avatar_url: string?
  role: "user" | "admin"
  language: string
  credits_balance: integer
  created_at: datetime
  updated_at: datetime
```

#### `POST /auth/login` — 用户登录

- Auth: 无

```yaml
Request:
  email: string (email format, required)
  password: string (required)

Response 200:
  access_token: string
  refresh_token: string
  token_type: "bearer"
  expires_in: integer (seconds)
```

#### `POST /auth/refresh` — 刷新 Token

- Auth: 无 (使用 refresh_token)

```yaml
Request:
  refresh_token: string (required)

Response 200:
  access_token: string
  refresh_token: string
  token_type: "bearer"
  expires_in: integer
```

#### `GET /auth/me` — 当前用户信息

- Auth: JWT

```yaml
Response 200: UserResponse
```

#### `PUT /auth/me` — 更新用户信息

- Auth: JWT

```yaml
Request:
  name: string? (1-100)
  company: string?
  avatar_url: string?
  language: "zh" | "en"

Response 200: UserResponse
```

#### `PUT /auth/password` — 修改密码

- Auth: JWT

```yaml
Request:
  current_password: string (required)
  new_password: string (min: 8, required)

Response 200:
  message: "Password updated"
```

---

### 3.2 招标机会 (`/opportunities`)

#### `GET /opportunities` — 招标机会列表

- Auth: JWT

```yaml
Query:
  search: string?              # 关键词搜索
  source: "adb"|"wb"|"un"     # 默认 "adb"
  status: "open"|"closed"     # 默认 "open"  
  published_from: date?
  published_to: date?
  deadline_from: date?
  deadline_to: date?
  country: string?
  sector: string?
  sort_by: "relevance"|"published_at"|"deadline"  # 默认 "relevance"
  sort_order: "asc"|"desc"    # 默认 "desc"
  page: integer (≥1)          # 默认 1
  page_size: integer (1-100)  # 默认 20

Response 200: PaginatedResponse<Opportunity>
```

**Opportunity Schema**:
```yaml
id: uuid
source: "adb" | "wb" | "un"
external_id: string?
url: string?
title: string
project_number: string?
description: string?
organization: string?
published_at: datetime?
deadline: datetime?
budget_min: number?
budget_max: number?
currency: string
location: string?
country: string?
sector: string?
procurement_type: string?
status: "open" | "closed" | "cancelled"
created_at: datetime
updated_at: datetime
```

#### `GET /opportunities/{id}` — 招标机会详情

- Auth: JWT

#### `POST /opportunities` — 创建招标机会 (管理员)

- Auth: JWT + Admin
- Status: 201

#### `PUT /opportunities/{id}` — 更新招标机会 (管理员)

- Auth: JWT + Admin

---

### 3.3 项目管理 (`/projects`)

#### `GET /projects` — 项目列表

- Auth: JWT
- 仅返回当前用户的项目

```yaml
Query:
  status: string?
  institution: string?
  page: integer
  page_size: integer

Response 200: PaginatedResponse<ProjectResponse>
```

#### `GET /projects/{id}` — 项目详情

- Auth: JWT (owner only)

```yaml
Response 200: ProjectDetailResponse
  # extends ProjectResponse
  opportunity: Opportunity?
  documents_count: integer
  bid_documents_count: integer
  analysis_status: string?
  sections_completed: integer
  total_sections: integer
```

#### `POST /projects` — 创建项目

- Auth: JWT
- Status: 201

```yaml
Request:
  name: string (1-200, required)
  description: string?
  institution: "adb" | "wb" | "un" (default: "adb")
  opportunity_id: uuid?

Response 201: ProjectResponse
```

#### `PUT /projects/{id}` — 更新项目

- Auth: JWT (owner only)

```yaml
Request: (all optional)
  name: string?
  description: string?
  status: project_status?
  institution: string?

Response 200: ProjectResponse
```

#### `DELETE /projects/{id}` — 删除项目

- Auth: JWT (owner only)
- Status: 204

#### `POST /projects/{id}/save` — 确认保存项目

- Auth: JWT

---

### 3.4 项目文档 (`/projects/{project_id}/documents`)

#### `POST /projects/{project_id}/documents` — 上传文档

- Auth: JWT
- Content-Type: multipart/form-data

```yaml
FormData:
  file: binary (PDF, ≤50MB, required)
  doc_type: "tor"|"rfp"|"company_profile"|"cv"|"past_project"|"reference"|"other"
  auto_process: boolean (default: true)

Response 201:
  id: uuid
  filename: string
  file_size: integer
  doc_type: string
  parse_status: string
  ocr_required: boolean
  message: string
```

#### `GET /projects/{project_id}/documents` — 文档列表

- Auth: JWT

```yaml
Query:
  doc_type: string?

Response 200:
  items: DocumentResponse[]
  total: integer
```

#### `GET /projects/{project_id}/documents/{id}` — 文档详情

- Auth: JWT

#### `DELETE /projects/{project_id}/documents/{id}` — 删除文档

- Auth: JWT
- Status: 204

#### `GET /projects/{project_id}/documents/{id}/download` — 下载文档

- Auth: JWT
- Response: binary (application/pdf)

#### `POST /projects/{project_id}/documents/{id}/process` — 触发处理

- Auth: JWT

#### `GET /projects/{project_id}/documents/{id}/status` — 处理状态

- Auth: JWT

---

### 3.5 招标文件 (`/bid-documents`)

#### `POST /bid-documents/projects/{project_id}/upload` — 上传招标文件

- Auth: JWT
- Content-Type: multipart/form-data

```yaml
FormData:
  files: binary[] (PDF, ≤50MB each, 多文件)
  language: string (default: "en")
  institution: string?

Response 201:
  documents: BidDocumentResponse[]
  message: string
```

**BidDocumentResponse Schema**:
```yaml
id: uuid
project_id: uuid
filename: string
file_size: integer
status: "pending"|"processing"|"completed"|"partial"|"failed"
processing_progress: integer (0-100)
page_count: integer?
chunk_count: integer?
vectorized_chunk_count: integer?
is_scanned: boolean
original_language: string
detected_institution: string?
ai_overview: string?
ai_reading_tips: string?
error_message: string?
created_at: datetime
processed_at: datetime?
```

#### `GET /bid-documents/projects/{project_id}` — 项目的招标文件列表

- Auth: JWT

```yaml
Response 200:
  items: BidDocumentResponse[]
  total: integer
  stats:
    total: integer
    pending: integer
    processing: integer
    completed: integer
    failed: integer
```

#### `GET /bid-documents/{id}` — 招标文件详情

- Auth: JWT

#### `GET /bid-documents/{id}/progress` — 处理进度

- Auth: JWT

#### `GET /bid-documents/{id}/structure` — 文档章节结构

- Auth: JWT

```yaml
Response 200:
  document_id: uuid
  filename: string
  page_count: integer
  sections:
    - id: uuid
      section_type: string
      title: string?
      start_page: integer
      end_page: integer
      content_preview: string?
      ai_summary: string?
      reading_guide: string?
```

#### `POST /bid-documents/{id}/reprocess` — 重新处理

- Auth: JWT

#### `DELETE /bid-documents/{id}` — 删除

- Auth: JWT
- Status: 204

#### `POST /bid-documents/projects/{project_id}/search` — 向量搜索

- Auth: JWT

```yaml
Request:
  query: string (1-1000, required)
  section_types: string[]?
  top_k: integer (1-20, default: 5)
  translate: boolean (default: true)

Response 200:
  results:
    - chunk_id: uuid
      content: string
      translation: string?
      page_number: integer
      section_type: string
      section_title: string?
      filename: string
      document_id: uuid
      similarity: float
  total: integer
```

#### `POST /bid-documents/projects/{project_id}/ask` — 文档问答 (RAG)

- Auth: JWT

```yaml
Request:
  question: string (1-2000, required)
  section_types: string[]?
  top_k: integer (1-10, default: 5)
  translate: boolean (default: true)

Response 200:
  answer: string
  translated_answer: string?
  sources:
    - index: integer
      section_type: string
      section_title: string?
      page_number: integer
      filename: string
      document_id: uuid
      similarity: float
```

#### `GET /bid-documents/projects/{project_id}/deep-analysis` — 深度分析结果

- Auth: JWT

#### `POST /bid-documents/projects/{project_id}/generate-analysis` — 生成深度分析

- Auth: JWT

```yaml
Request:
  force_refresh: boolean (default: false)

Response 200:
  id: uuid
  project_id: uuid
  qualification_requirements: object?
  evaluation_criteria: object?
  submission_checklist: object?
  key_dates: object?
  budget_info: object?
  special_notes: string?
  risk_assessment: object?
  model_used: string?
  tokens_consumed: integer
  created_at: datetime
```

#### `GET /bid-documents/projects/{project_id}/analysis` — 获取分析结果

- Auth: JWT

#### `GET /bid-documents/meta/section-types` — Section 类型元数据

- Auth: 无

---

### 3.6 招标分析 (`/projects/{project_id}/analysis`)

#### `POST /projects/{project_id}/analysis` — 触发 AI 分析

- Auth: JWT

```yaml
Request:
  force_refresh: boolean (default: false)

Response 200: BidAnalysisResponse
```

#### `GET /projects/{project_id}/analysis` — 获取分析结果

- Auth: JWT

```yaml
Response 200: BidAnalysisResponse
  id: uuid
  project_id: uuid
  qualification_requirements: object?
  evaluation_criteria: object?
  evaluation_methodology: object?
  commercial_terms: object?
  submission_checklist: object?
  key_dates: object?
  budget_info: object?
  special_notes: string?
  quality_review: object?
  model_used: string?
  tokens_consumed: integer
  created_at: datetime
  updated_at: datetime
```

---

### 3.7 投标计划 (`/projects/{project_id}/bid-plan`)

#### `GET /projects/{project_id}/bid-plan` — 获取投标计划

- Auth: JWT

```yaml
Response 200: BidPlanResponse
  id: uuid
  project_id: uuid
  name: string
  description: string?
  total_tasks: integer
  completed_tasks: integer
  progress_percentage: float
  generated_by_ai: boolean
  model_used: string?
  tasks: TaskResponse[]
  created_at: datetime
  updated_at: datetime
```

#### `POST /projects/{project_id}/bid-plan/generate` — AI 生成投标计划

- Auth: JWT

```yaml
Request:
  deadline: date?
  force_refresh: boolean (default: false)

Response 200: BidPlanResponse
```

#### `POST /projects/{project_id}/bid-plan/tasks` — 添加任务

- Auth: JWT
- Status: 201

```yaml
Request:
  title: string (required)
  description: string?
  category: string? (default: "documents")
  priority: "low"|"medium"|"high"|"critical" (default: "medium")
  assignee: string?
  due_date: date?
  notes: string?

Response 201: TaskResponse
```

#### `PATCH /bid-plan/tasks/{task_id}` — 更新任务

- Auth: JWT

```yaml
Request: (all optional)
  title: string?
  description: string?
  category: string?
  status: "pending"|"in_progress"|"completed"|"skipped"
  priority: "low"|"medium"|"high"|"critical"
  assignee: string?
  due_date: date?
  notes: string?

Response 200: TaskResponse
```

#### `DELETE /bid-plan/tasks/{task_id}` — 删除任务

- Auth: JWT
- Status: 204

#### `POST /projects/{project_id}/bid-plan/reorder` — 任务排序

- Auth: JWT

```yaml
Request:
  task_orders:
    - task_id: uuid
      sort_order: integer

Response 200:
  message: "Reordered"
```

---

### 3.8 评标预测 (`/projects/{project_id}/prediction`)

#### `POST /projects/{project_id}/prediction` — 生成评标预测

- Auth: JWT

```yaml
Request:
  force_refresh: boolean (default: false)

Response 200: BidPredictionResponse
  id: uuid
  project_id: uuid
  overall_score: integer? (0-100)
  technical_score: integer?
  commercial_score: integer?
  win_probability: integer? (0-100)
  weaknesses: object[]?
  recommendations: object[]?
  competitive_analysis: object?
  model_used: string?
  confidence_level: "high"|"medium"|"low"
  status: string
  created_at: datetime
```

#### `GET /projects/{project_id}/prediction` — 获取预测结果

- Auth: JWT

#### `GET /projects/{project_id}/prediction/quick` — 快速评估

- Auth: JWT

---

### 3.9 质量审查 (`/projects/{project_id}/quality-review`)

#### `POST /projects/{project_id}/quality-review` — 请求质量审查

- Auth: JWT

```yaml
Query:
  quick_mode: boolean (default: false)
  force_refresh: boolean (default: false)

Response 200:
  success: true
  data: QualityReviewResult
```

#### `GET /projects/{project_id}/quality-review` — 审查结果

- Auth: JWT

#### `GET /projects/{project_id}/quality-review/summary` — 审查摘要

- Auth: JWT

#### `POST /projects/{project_id}/quality-review/check-completeness` — 完整性

- Auth: JWT

#### `POST /projects/{project_id}/quality-review/check-compliance` — 合规性

- Auth: JWT

#### `POST /projects/{project_id}/quality-review/check-consistency` — 一致性

- Auth: JWT

#### `POST /projects/{project_id}/quality-review/flag-risks` — 风险识别

- Auth: JWT

---

### 3.10 标书编制指导 (`/guidance`)

#### `POST /guidance/ask` — 提交指导请求

- Auth: JWT
- 用户在问答区提交问题或需求，系统智能路由到 prompt 回答或 Skills 分析

```yaml
Request:
  project_id: uuid (required)
  message: string (required)        # 用户消息
  context: object?                  # 可选上下文
    section_id: string?             # 当前所在章节
    intent: string?                 # 前端预判意图 (guidance/review/question)

Response 200:
  message_id: string
  response: string                  # AI 回答内容
  route_type: "prompt"|"skill"      # 实际路由方式
  skill_used: string?               # 使用的 Skill 名称
  tokens_consumed: integer
  credits_consumed: integer
```

#### `POST /guidance/ask-stream` — 流式指导请求 (SSE)

- Auth: JWT
- Response: `text/event-stream`

```
event: thinking
data: {"message": "正在分析您的需求..."}

event: chunk
data: {"content": "根据招标文件要求，技术方案章节应包含..."}

event: reference
data: {"source": "TOR Section 5.2", "content": "..."}

event: complete
data: {"message_id": "xxx", "route_type": "skill", "tokens_consumed": 1500}

event: error
data: {"code": "LLM_ERROR", "message": "..."}
```

#### `POST /guidance/section-guidance` — 章节编写指导

- Auth: JWT
- 获取特定章节的结构化编写指导

```yaml
Request:
  project_id: uuid (required)
  section_id: string (required)

Response 200:
  section_id: string
  title: string
  guidance: object
    format_requirements: string[]   # 格式要求
    content_outline: string[]       # 内容要点
    scoring_alignment: object[]     # 评分对标建议
    template_references: string[]   # 模板参考片段
    common_pitfalls: string[]       # 常见错误提醒
    word_count_target: integer
  tokens_consumed: integer
```

#### `POST /guidance/review-draft` — 审查用户草稿

- Auth: JWT

```yaml
Request:
  project_id: uuid (required)
  section_id: string (required)
  draft_content: string (required)  # 用户编写的草稿内容

Response 200:
  section_id: string
  overall_score: integer (0-100)
  format_compliance: object
  content_completeness: object
  scoring_alignment: object
  language_quality: object
  specific_feedback: string[]
  priority_improvements: string[]
  tokens_consumed: integer
```

#### `GET /guidance/{project_id}/document-structure` — 获取投标文件结构

- Auth: JWT

```yaml
Response 200:
  project_id: uuid
  title: string
  sections: object[]
    - id: string
      title: string
      requirements: string
      scoring_weight: number
      format_requirements: string[]
      status: "not_started"|"drafting"|"reviewed"|"completed"
```

#### `GET /guidance/{project_id}/conversation` — 获取指导对话历史

- Auth: JWT

```yaml
Query:
  page: integer?
  page_size: integer?

Response 200:
  messages: object[]
    - id: string
      role: "user"|"assistant"
      content: string
      route_type: "prompt"|"skill"?
      skill_used: string?
      created_at: datetime
  total: integer
```

---

### 3.11 知识库 (`/knowledge-bases`)

#### `GET /knowledge-bases` — 知识库列表

- Auth: JWT

```yaml
Query:
  institution: "adb"|"wb"|"un"?
  kb_type: "guide"|"review"|"template"?

Response 200:
  items: KnowledgeBaseResponse[]
  total: integer
```

#### `GET /knowledge-bases/{id}` — 知识库详情

- Auth: JWT

#### `POST /knowledge-bases` — 创建知识库 (管理员)

- Auth: JWT + Admin
- Status: 201

#### `DELETE /knowledge-bases/{id}` — 删除知识库 (管理员)

- Auth: JWT + Admin
- Status: 204

#### `POST /knowledge-bases/{id}/documents` — 上传文档

- Auth: JWT
- Content-Type: multipart/form-data

#### `GET /knowledge-bases/{id}/documents` — 文档列表

- Auth: JWT

#### `POST /knowledge-bases/{id}/documents/{doc_id}/process` — 处理文档

- Auth: JWT

#### `DELETE /knowledge-bases/{id}/documents/{doc_id}` — 删除文档

- Auth: JWT
- Status: 204

#### `POST /knowledge-bases/{id}/search` — 向量搜索

- Auth: JWT

```yaml
Request:
  query: string (1-1000, required)
  limit: integer (1-20, default: 5)
  score_threshold: float (0-1, default: 0.5)

Response 200:
  query: string
  results:
    - chunk_id: uuid
      content: string
      document_name: string
      page_number: integer?
      score: float
  total: integer
```

#### `POST /knowledge-bases/{id}/qa` — 知识库问答

- Auth: JWT

```yaml
Request:
  question: string (1-2000, required)
  include_sources: boolean (default: true)
  max_sources: integer (1-10, default: 5)

Response 200:
  question: string
  answer: string
  sources:
    - document_name: string
      page_number: integer?
      excerpt: string
      relevance_score: float
  credits_consumed: integer
```

#### `POST /knowledge-bases/{id}/import` — 批量导入 (管理员)

- Auth: JWT + Admin

#### `GET /knowledge-bases/{institution}/bid-steps` — 投标流程

- Auth: JWT

#### `GET /knowledge-bases/{institution}/review-criteria` — 评审标准

- Auth: JWT

#### `POST /knowledge-bases/{institution}/review-section` — 审查章节

- Auth: JWT

---

### 3.12 支付 (`/payments`)

#### `GET /payments/packages` — 充值套餐列表

- Auth: JWT

```yaml
Response 200:
  - id: uuid
    name: string
    description: string?
    credit_amount: integer
    bonus_credits: integer
    price: number
    currency: string
```

#### `POST /payments/orders` — 创建支付订单

- Auth: JWT

```yaml
Request:
  amount: number (required)
  payment_method: "alipay"|"wechat" (required)
  product_type: "credit_recharge"|"subscription" (required)
  product_id: uuid?
  description: string?

Response 201:
  order_no: string
  amount: number
  payment_method: string
  status: string
  pay_url: string?
  pay_params: object?
```

#### `GET /payments/orders/{order_no}` — 查询订单状态

- Auth: JWT

#### `POST /payments/orders/{order_no}/refund` — 申请退款

- Auth: JWT

#### `GET /payments/history` — 支付历史

- Auth: JWT

```yaml
Query:
  page: integer
  page_size: integer

Response 200:
  orders: PaymentOrderResponse[]
  transactions: TransactionResponse[]
  total: integer
  page: integer
  page_size: integer
```

#### `POST /payments/webhooks/alipay` — 支付宝回调

- Auth: 无 (签名验证)

#### `POST /payments/webhooks/wechat` — 微信支付回调

- Auth: 无 (签名验证)

---

### 3.13 统计 (`/stats`)

#### `GET /stats/overview` — 运营概览 (管理员)

- Auth: JWT + Admin

```yaml
Query:
  date_from: date?
  date_to: date?

Response 200:
  users: { total, new_today, active_today }
  projects: { total, active, completed }
  opportunities: { total, open }
  revenue: { total, today }
```

#### `GET /stats/users` — 用户统计 (管理员)

- Auth: JWT + Admin

#### `GET /stats/opportunities` — 招标统计 (管理员)

- Auth: JWT + Admin

#### `GET /stats/projects` — 项目统计 (管理员)

- Auth: JWT + Admin

#### `GET /stats/finances` — 财务统计 (管理员)

- Auth: JWT + Admin

#### `GET /stats/usage` — 使用统计 (管理员)

- Auth: JWT + Admin

#### `GET /stats/my-usage` — 个人使用统计

- Auth: JWT

---

### 3.14 工作流 (`/projects/{project_id}/workflow`)

#### `GET /projects/{project_id}/workflow` — 工作流状态

- Auth: JWT

```yaml
Response 200:
  current_step: string
  workflow_state: object
  available_steps: string[]
  completed_steps: string[]
```

**工作流步骤**: `document_upload` → `tor_analysis` → `company_profile` → `team_composition` → `methodology` → `work_plan` → `budget` → `review_submit`

#### `PUT /projects/{project_id}/workflow` — 更新工作流步骤

- Auth: JWT

```yaml
Request:
  step: string (required)
  data: object (required)

Response 200: WorkflowStateResponse
```

#### `POST /projects/{project_id}/analyze-tor` — TOR 分析

- Auth: JWT

```yaml
Response 200:
  summary: string
  key_requirements: string[]
  evaluation_criteria: object[]
  submission_requirements: object
  timeline: object
  budget_info: object?
```

#### `POST /projects/{project_id}/qa` — 项目文档问答

- Auth: JWT

```yaml
Request:
  question: string (1-2000, required)
  use_knowledge_base: boolean (default: false)
  top_k: integer (1-20, default: 5)

Response 200:
  answer: string
  sources: object[]
  from_knowledge_base: boolean
```

---

### 3.15 健康检查

#### `GET /health` — 健康检查

- Auth: 无

```yaml
Response 200:
  status: "healthy"
  version: string
  database: "connected" | "disconnected"
  redis: "connected" | "disconnected"
```

---

## 4. 通用 Schema 定义

### 4.1 分页包装

```yaml
PaginatedResponse<T>:
  items: T[]
  total: integer
  page: integer (≥1)
  page_size: integer (1-100)
  pages: integer
```

### 4.2 错误响应

```yaml
ErrorResponse:
  code: string    # 机器可读错误码
  message: string # 人类可读消息
  detail: any?    # 附加详情

# 错误码枚举:
# NOT_FOUND, UNAUTHORIZED, FORBIDDEN, VALIDATION_ERROR,
# INSUFFICIENT_CREDITS, RATE_LIMITED, EXTERNAL_SERVICE_ERROR,
# INTERNAL_ERROR
```

### 4.3 HTTP 状态码

| 状态码 | 含义 | 使用场景 |
|--------|------|---------|
| 200 | OK | 查询/更新成功 |
| 201 | Created | 创建成功 |
| 204 | No Content | 删除成功 |
| 400 | Bad Request | 请求格式错误 |
| 401 | Unauthorized | 未提供/无效 Token |
| 402 | Payment Required | 积分不足 |
| 403 | Forbidden | 无权限 (非 owner/非 admin) |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 资源已存在 (注册重复邮箱) |
| 422 | Unprocessable Entity | 请求体校验失败 |
| 429 | Too Many Requests | 速率限制 |
| 500 | Internal Server Error | 服务器错误 |
| 502 | Bad Gateway | 外部服务 (LLM/Embedding) 失败 |

---

## 5. 端点统计

| 模块 | 端点数 | Auth |
|------|--------|------|
| Auth | 6 | 混合 |
| Opportunities | 4 | JWT (Admin for write) |
| Projects | 7 | JWT (owner) |
| Project Documents | 7 | JWT |
| Bid Documents | 14 | JWT |
| Bid Analysis | 2 | JWT |
| Bid Plan | 6 | JWT |
| Bid Prediction | 3 | JWT |
| Quality Review | 7 | JWT |
| Generate | 7 | JWT |
| Knowledge Base | 15 | JWT (Admin for manage) |
| Payments | 7 | JWT (webhooks public) |
| Stats | 7 | JWT (Admin) |
| Workflow | 4 | JWT |
| Health | 1 | 无 |
| **总计** | **97** | |
