# BidAgent V2 — 数据模型设计

> 版本: 2.0.0 | 日期: 2026-02-11 | 状态: Draft

## 1. 设计原则

1. **统一主键**: 所有表使用 `UUID` 主键 (`uuid_generate_v4()`)
2. **统一时间戳**: `TIMESTAMP WITH TIME ZONE`，默认 `now()`
3. **统一枚举**: 使用 PG 原生 `ENUM` 类型，不混用 CHECK 约束
4. **向量维度**: 固定 `1024` (腾讯混元 hunyuan-embedding)
5. **向量索引**: 统一 HNSW (`m=16, ef_construction=64, vector_cosine_ops`)
6. **数据库迁移**: Alembic 版本化管理，首个迁移包含完整 DDL
7. **软删除**: 关键业务表通过 `deleted_at` 列支持软删除（可选）

---

## 2. 枚举类型

```sql
-- 用户角色
CREATE TYPE user_role AS ENUM ('user', 'admin');

-- 招标来源
CREATE TYPE opportunity_source AS ENUM ('adb', 'wb', 'un');

-- 招标状态
CREATE TYPE opportunity_status AS ENUM ('open', 'closed', 'cancelled');

-- 项目状态
CREATE TYPE project_status AS ENUM (
  'draft', 'analyzing', 'guiding', 'review', 'submitted', 'won', 'lost'
);

-- 文档类型
CREATE TYPE document_type AS ENUM (
  'tor', 'rfp', 'company_profile', 'cv', 'past_project', 'reference', 'other'
);

-- 处理状态 (通用)
CREATE TYPE processing_status AS ENUM (
  'pending', 'processing', 'completed', 'partial', 'failed'
);

-- 投标计划任务状态
CREATE TYPE task_status AS ENUM ('pending', 'in_progress', 'completed', 'skipped');

-- 投标计划任务优先级
CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high', 'critical');

-- 支付方式
CREATE TYPE payment_method AS ENUM ('alipay', 'wechat', 'stripe');

-- 支付状态
CREATE TYPE payment_status AS ENUM (
  'pending', 'processing', 'success', 'failed', 'closed', 'refunded'
);

-- 产品类型
CREATE TYPE product_type AS ENUM ('credit_recharge', 'subscription');

-- 交易类型
CREATE TYPE transaction_type AS ENUM ('income', 'expense');

-- 使用日志动作
CREATE TYPE action_type AS ENUM ('analysis', 'create', 'export', 'view', 'download');

-- 招标文件 Section 类型
CREATE TYPE section_type AS ENUM (
  'section_1_itb', 'section_2_bds', 'section_3_qualification', 'section_4_forms',
  'section_5_countries', 'part_1_procedures', 'part_2_requirements',
  'part_3_contract', 'appendix', 'unknown'
);

-- 知识库类型
CREATE TYPE kb_type AS ENUM ('guide', 'review', 'template');
```

---

## 3. 表结构定义

### 3.1 用户与认证

#### `users` — 用户表

| 列名 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PK | `uuid_generate_v4()` | |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | | 登录邮箱 |
| `hashed_password` | VARCHAR(255) | NOT NULL | | bcrypt 哈希 |
| `name` | VARCHAR(100) | NOT NULL | | 显示名称 |
| `company` | VARCHAR(200) | | | 所属公司 |
| `avatar_url` | VARCHAR(500) | | | 头像 URL |
| `role` | user_role | NOT NULL | `'user'` | 用户/管理员 |
| `language` | VARCHAR(10) | NOT NULL | `'zh'` | UI 语言偏好 |
| `credits_balance` | INTEGER | NOT NULL | `0` | 积分余额 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | |

---

### 3.2 招标机会

#### `opportunities` — 招标机会表

> V2 合并 V1 的 `opportunities` + `bid_opportunities` 为单一表

| 列名 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PK | `uuid_generate_v4()` | |
| `source` | opportunity_source | NOT NULL, INDEX | | 来源: adb/wb/un |
| `external_id` | VARCHAR(100) | INDEX | | 原站 ID |
| `url` | VARCHAR(500) | | | 原文链接 |
| `title` | VARCHAR(500) | NOT NULL | | 标题 |
| `project_number` | VARCHAR(100) | INDEX | | 项目编号 |
| `description` | TEXT | | | 描述 |
| `organization` | VARCHAR(200) | | | 发布机构 |
| `published_at` | TIMESTAMPTZ | INDEX | | 发布时间 |
| `deadline` | TIMESTAMPTZ | INDEX | | 截止时间 |
| `budget_min` | NUMERIC(15,2) | | | 预算下限 |
| `budget_max` | NUMERIC(15,2) | | | 预算上限 |
| `currency` | VARCHAR(3) | NOT NULL | `'USD'` | 币种 |
| `location` | VARCHAR(300) | | | 工作地点 |
| `country` | VARCHAR(100) | INDEX | | 国家 |
| `sector` | VARCHAR(100) | INDEX | | 行业 |
| `procurement_type` | VARCHAR(100) | | | 采购类型 |
| `status` | opportunity_status | NOT NULL | `'open'` | 状态 |
| `search_vector` | TSVECTOR | GIN INDEX | | 全文搜索 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | |

**索引**:
- `idx_opp_source_status (source, status)`
- `idx_opp_source_published (source, published_at DESC)`
- `idx_opp_deadline (deadline)`
- `idx_opp_search_vector USING GIN (search_vector)`

**约束**:
- `CHECK (budget_min >= 0)`
- `CHECK (budget_max IS NULL OR budget_max >= budget_min)`
- `UNIQUE (source, external_id)`

---

### 3.3 项目管理

#### `projects` — 投标项目表

| 列名 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PK | `uuid_generate_v4()` | |
| `name` | VARCHAR(200) | NOT NULL | | 项目名称 |
| `description` | TEXT | | | 项目描述 |
| `status` | project_status | NOT NULL | `'draft'` | 项目状态 |
| `opportunity_id` | UUID | FK → opportunities(id) SET NULL, INDEX | | 关联招标机会 |
| `user_id` | UUID | FK → users(id) CASCADE, NOT NULL, INDEX | | 项目所有者 |
| `progress` | INTEGER | NOT NULL | `0` | 完成进度 0-100 |
| `current_step` | VARCHAR(50) | NOT NULL | `'upload'` | 当前工作流步骤 |
| `workflow_state` | JSONB | NOT NULL | `'{}'` | 工作流中间状态 |
| `institution` | VARCHAR(10) | NOT NULL | `'adb'` | 机构: adb/wb/un |
| `is_saved` | BOOLEAN | NOT NULL | `false` | 用户是否确认保存 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | |

**索引**: `idx_proj_user_status (user_id, status)`, `idx_proj_institution (institution)`

---

### 3.4 文档处理

#### `bid_documents` — 招标文件表

| 列名 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PK | `uuid_generate_v4()` | |
| `project_id` | UUID | FK → projects(id) CASCADE, NOT NULL, INDEX | | |
| `filename` | VARCHAR(255) | NOT NULL | | 存储文件名 |
| `original_filename` | VARCHAR(255) | NOT NULL | | 原始文件名 |
| `file_path` | VARCHAR(500) | NOT NULL | | 存储路径 |
| `file_size` | BIGINT | | | 文件大小 (bytes) |
| `file_hash` | VARCHAR(64) | | | SHA256 去重 |
| `status` | processing_status | NOT NULL | `'pending'` | 处理状态 |
| `processing_progress` | INTEGER | NOT NULL | `0` | 处理进度 0-100 |
| `page_count` | INTEGER | | | 总页数 |
| `processed_pages` | INTEGER | NOT NULL | `0` | 已处理页数 |
| `chunk_count` | INTEGER | NOT NULL | `0` | 分块总数 |
| `vectorized_chunk_count` | INTEGER | NOT NULL | `0` | 已向量化分块数 |
| `error_message` | TEXT | | | 错误信息 |
| `is_scanned` | BOOLEAN | NOT NULL | `false` | 是否扫描件 |
| `ocr_confidence` | FLOAT | | | OCR 置信度 |
| `original_language` | VARCHAR(10) | NOT NULL | `'en'` | 原始语言 |
| `uploaded_by` | UUID | FK → users(id) SET NULL | | 上传者 |
| `ai_overview` | TEXT | | | AI 文档概览 |
| `ai_reading_tips` | TEXT | | | AI 阅读建议 |
| `detected_institution` | VARCHAR(20) | INDEX | | 检测到的机构 |
| `analysis_generated_at` | TIMESTAMPTZ | | | AI 分析完成时间 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | |
| `processed_at` | TIMESTAMPTZ | | | 处理完成时间 |

**索引**: `idx_bd_project_status (project_id, status)`, `idx_bd_file_hash (project_id, file_hash)`
**约束**: `CHECK (processing_progress >= 0 AND processing_progress <= 100)`

#### `bid_document_sections` — 招标文件 Section 表

| 列名 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PK | `uuid_generate_v4()` | |
| `bid_document_id` | UUID | FK → bid_documents(id) CASCADE, NOT NULL, INDEX | | |
| `section_type` | section_type | NOT NULL | | Section 类型 |
| `section_title` | VARCHAR(500) | | | 原始标题 |
| `section_number` | VARCHAR(20) | | | "Section 1", "Part 2" |
| `start_page` | INTEGER | NOT NULL | | 起始页 |
| `end_page` | INTEGER | NOT NULL | | 结束页 |
| `content_preview` | TEXT | | | 前 500 字符预览 |
| `detected_by` | VARCHAR(20) | NOT NULL | `'regex'` | 检测方式: regex/llm |
| `confidence` | FLOAT | | | 置信度 |
| `ai_summary` | TEXT | | | AI 章节摘要 |
| `reading_guide` | TEXT | | | AI 阅读指南 |
| `analysis_generated_at` | TIMESTAMPTZ | | | AI 分析时间 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | |

**索引**: `idx_bds_doc_type (bid_document_id, section_type)`, `idx_bds_page_range (bid_document_id, start_page, end_page)`

#### `bid_document_chunks` — 招标文件分块表 (含向量)

| 列名 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PK | `uuid_generate_v4()` | |
| `bid_document_id` | UUID | FK → bid_documents(id) CASCADE, NOT NULL, INDEX | | |
| `project_id` | UUID | FK → projects(id) CASCADE, NOT NULL, INDEX | | 冗余FK加速检索 |
| `section_id` | UUID | FK → bid_document_sections(id) SET NULL, INDEX | | |
| `content` | TEXT | NOT NULL | | 分块文本 |
| `chunk_index` | INTEGER | NOT NULL | | 在文档中的顺序 |
| `page_number` | INTEGER | NOT NULL | | 所在页码 |
| `start_char` | INTEGER | | | 起始字符位置 |
| `end_char` | INTEGER | | | 结束字符位置 |
| `section_type` | VARCHAR(50) | | | 冗余: Section 类型 |
| `clause_reference` | VARCHAR(100) | | | 条款引用: "ITB 12.1" |
| `embedding` | VECTOR(1024) | | | 混元嵌入向量 |
| `chunk_metadata` | JSONB | | | 附加元数据 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | |

**索引**:
- `idx_bdc_embedding USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64)`
- `idx_bdc_project_section (project_id, section_type)`
- `idx_bdc_page (bid_document_id, page_number)`

#### `project_documents` — 项目文档表 (公司资料/CV 等)

| 列名 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PK | `uuid_generate_v4()` | |
| `project_id` | UUID | FK → projects(id) CASCADE, NOT NULL, INDEX | | |
| `filename` | VARCHAR(255) | NOT NULL | | 存储文件名 |
| `original_filename` | VARCHAR(255) | NOT NULL | | 原始文件名 |
| `file_path` | VARCHAR(500) | NOT NULL | | 存储路径 |
| `file_size` | INTEGER | | | 文件大小 |
| `mime_type` | VARCHAR(100) | NOT NULL | `'application/pdf'` | MIME 类型 |
| `file_hash` | VARCHAR(64) | | | SHA256 去重 |
| `doc_type` | document_type | NOT NULL | `'other'` | 文档类型 |
| `parse_status` | processing_status | NOT NULL | `'pending'` | 解析状态 |
| `parse_error` | TEXT | | | 解析错误 |
| `parsed_content` | TEXT | | | 提取的纯文本 |
| `ocr_required` | BOOLEAN | NOT NULL | `false` | 需要 OCR |
| `ocr_confidence` | FLOAT | | | OCR 置信度 |
| `embedding_status` | processing_status | NOT NULL | `'pending'` | 向量化状态 |
| `chunk_count` | INTEGER | NOT NULL | `0` | 分块数 |
| `page_count` | INTEGER | | | 页数 |
| `language` | VARCHAR(10) | | | 检测语言 |
| `doc_metadata` | JSONB | NOT NULL | `'{}'` | 附加元数据 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | |
| `processed_at` | TIMESTAMPTZ | | | 处理完成时间 |

**索引**: `idx_pd_project_type (project_id, doc_type)`, `idx_pd_file_hash (project_id, file_hash)`

#### `project_document_chunks` — 项目文档分块表 (含向量)

| 列名 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PK | `uuid_generate_v4()` | |
| `document_id` | UUID | FK → project_documents(id) CASCADE, NOT NULL, INDEX | | |
| `project_id` | UUID | FK → projects(id) CASCADE, NOT NULL, INDEX | | |
| `content` | TEXT | NOT NULL | | 分块文本 |
| `chunk_index` | INTEGER | NOT NULL | | 序号 |
| `page_number` | INTEGER | | | 页码 |
| `start_char` | INTEGER | | | |
| `end_char` | INTEGER | | | |
| `embedding` | VECTOR(1024) | | | 混元嵌入向量 |
| `chunk_metadata` | JSONB | | `'{}'` | |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | |

**索引**: `idx_pdc_embedding USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64)`

#### `translation_cache` — 翻译缓存表

| 列名 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PK | `uuid_generate_v4()` | |
| `content_hash` | VARCHAR(64) | NOT NULL, INDEX | | 原文 MD5 |
| `source_lang` | VARCHAR(10) | NOT NULL | | 源语言 |
| `target_lang` | VARCHAR(10) | NOT NULL | | 目标语言 |
| `original_text` | TEXT | NOT NULL | | 原文 |
| `translated_text` | TEXT | NOT NULL | | 译文 |
| `chunk_id` | UUID | FK → bid_document_chunks(id) CASCADE | | 关联分块 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | |

**约束**: `UNIQUE (content_hash, source_lang, target_lang)`

---

### 3.5 AI 分析

#### `bid_analyses` — 招标分析表 (每项目一条)

| 列名 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PK | `uuid_generate_v4()` | |
| `project_id` | UUID | FK → projects(id) CASCADE, NOT NULL, UNIQUE | | 每项目最多一条 |
| `qualification_requirements` | JSONB | | | 资质要求分析 |
| `evaluation_criteria` | JSONB | | | 评分标准提取 |
| `evaluation_methodology` | JSONB | | | 评标方法论 |
| `commercial_terms` | JSONB | | | 商务条款分析 |
| `submission_checklist` | JSONB | | | 提交清单 |
| `key_dates` | JSONB | | | 关键日期 |
| `budget_info` | JSONB | | | 预算信息 |
| `special_notes` | TEXT | | | 特殊说明 |
| `quality_review` | JSONB | | | AI 质量审查 |
| `raw_analysis` | TEXT | | | AI 原始响应文本 |
| `model_used` | VARCHAR(100) | | | 使用的模型 |
| `tokens_consumed` | INTEGER | NOT NULL | `0` | Token 消耗 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | |

#### `bid_predictions` — 评标预测表

| 列名 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PK | `uuid_generate_v4()` | |
| `project_id` | UUID | FK → projects(id) CASCADE, NOT NULL, INDEX | | |
| `overall_score` | INTEGER | | | 综合评分 0-100 |
| `technical_score` | INTEGER | | | 技术评分 |
| `commercial_score` | INTEGER | | | 商务评分 |
| `win_probability` | INTEGER | | | 中标概率 0-100 |
| `weaknesses` | JSONB | | | 薄弱环节 |
| `recommendations` | JSONB | | | 改进建议 |
| `competitive_analysis` | JSONB | | | 竞争分析 |
| `analysis_snapshot` | JSONB | | | 分析数据快照 |
| `model_used` | VARCHAR(100) | | | |
| `confidence_level` | VARCHAR(20) | | | high/medium/low |
| `analysis_version` | VARCHAR(20) | NOT NULL | `'1.0'` | |
| `status` | processing_status | NOT NULL | `'pending'` | |
| `error_message` | TEXT | | | |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | |

---

### 3.6 投标计划

#### `bid_plans` — 投标计划表 (每项目一个)

| 列名 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PK | `uuid_generate_v4()` | |
| `project_id` | UUID | FK → projects(id) CASCADE, NOT NULL, UNIQUE | | |
| `name` | VARCHAR(200) | NOT NULL | `'投标计划'` | |
| `description` | TEXT | | | |
| `total_tasks` | INTEGER | NOT NULL | `0` | 触发器自动更新 |
| `completed_tasks` | INTEGER | NOT NULL | `0` | 触发器自动更新 |
| `generated_by_ai` | BOOLEAN | NOT NULL | `true` | |
| `model_used` | VARCHAR(100) | | | |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | |

#### `bid_plan_tasks` — 投标计划任务表

| 列名 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PK | `uuid_generate_v4()` | |
| `plan_id` | UUID | FK → bid_plans(id) CASCADE, NOT NULL, INDEX | | |
| `title` | VARCHAR(500) | NOT NULL | | 任务标题 |
| `description` | TEXT | | | |
| `category` | VARCHAR(100) | | | documents/team/technical/... |
| `sort_order` | INTEGER | NOT NULL | `0` | 排序 |
| `status` | task_status | NOT NULL | `'pending'` | |
| `priority` | task_priority | NOT NULL | `'medium'` | |
| `assignee` | VARCHAR(200) | | | 负责人 |
| `due_date` | DATE | INDEX | | 截止日期 |
| `completed_at` | TIMESTAMPTZ | | | 完成时间 |
| `related_document` | VARCHAR(500) | | | 关联文档 |
| `reference_page` | INTEGER | | | 参考页码 |
| `notes` | TEXT | | | 备注 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | |

**索引**: `idx_bpt_plan_sort (plan_id, sort_order)`

**触发器**: INSERT/UPDATE/DELETE 后自动更新 `bid_plans.total_tasks` 和 `bid_plans.completed_tasks`

---

### 3.7 知识库

#### `knowledge_bases` — 知识库表

| 列名 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PK | `uuid_generate_v4()` | |
| `name` | VARCHAR(200) | NOT NULL | | 知识库名称 |
| `institution` | opportunity_source | NOT NULL, INDEX | | 所属机构 |
| `kb_type` | kb_type | NOT NULL, INDEX | | 类型 |
| `description` | TEXT | | | 描述 |
| `document_count` | INTEGER | NOT NULL | `0` | 文档数 |
| `chunk_count` | INTEGER | NOT NULL | `0` | 分块数 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | |

**索引**: `idx_kb_institution_type (institution, kb_type)`

**预置数据**:
```sql
INSERT INTO knowledge_bases (id, name, institution, kb_type) VALUES
  (gen_random_uuid(), 'ADB采购准则', 'adb', 'guide'),
  (gen_random_uuid(), 'ADB评标参考', 'adb', 'review'),
  (gen_random_uuid(), 'WB采购准则', 'wb', 'guide'),
  (gen_random_uuid(), 'WB评标参考', 'wb', 'review');
```

#### `knowledge_documents` — 知识库文档表

| 列名 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PK | `uuid_generate_v4()` | |
| `knowledge_base_id` | UUID | FK → knowledge_bases(id) CASCADE, NOT NULL, INDEX | | |
| `filename` | VARCHAR(255) | NOT NULL | | |
| `file_path` | VARCHAR(500) | NOT NULL | | |
| `file_size` | INTEGER | | | |
| `file_hash` | VARCHAR(64) | INDEX | | SHA256 去重 |
| `status` | processing_status | NOT NULL | `'pending'` | |
| `error_message` | TEXT | | | |
| `page_count` | INTEGER | | | |
| `chunk_count` | INTEGER | NOT NULL | `0` | |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | |
| `processed_at` | TIMESTAMPTZ | | | |

#### `knowledge_chunks` — 知识库分块表 (含向量)

| 列名 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PK | `uuid_generate_v4()` | |
| `document_id` | UUID | FK → knowledge_documents(id) CASCADE, NOT NULL, INDEX | | |
| `content` | TEXT | NOT NULL | | 分块文本 |
| `chunk_index` | INTEGER | NOT NULL | | 序号 |
| `page_number` | INTEGER | | | 页码 |
| `start_char` | INTEGER | | | |
| `end_char` | INTEGER | | | |
| `chunk_metadata` | JSONB | | | |
| `embedding` | VECTOR(1024) | | | 混元嵌入向量 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | |

**索引**:
- `idx_kc_embedding USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64)`
- `idx_kc_doc_page (document_id, page_number)`

---

### 3.8 专家管理

#### `experts` — 专家资料表

| 列名 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PK | `uuid_generate_v4()` | |
| `organization_id` | UUID | FK → users(id) CASCADE, NOT NULL, INDEX | | 所属组织/用户 |
| `name` | VARCHAR(200) | NOT NULL, INDEX | | 中文名 |
| `name_en` | VARCHAR(200) | | | 英文名 |
| `title` | VARCHAR(200) | | | 职称 |
| `nationality` | VARCHAR(100) | | | 国籍 |
| `date_of_birth` | DATE | | | 出生日期 |
| `email` | VARCHAR(200) | | | 邮箱 |
| `phone` | VARCHAR(50) | | | 电话 |
| `education_level` | VARCHAR(50) | | | bachelor/master/phd/other |
| `education_details` | JSONB | | | 教育经历 |
| `certifications` | JSONB | | | 资质证书 |
| `professional_memberships` | JSONB | | | 专业协会 |
| `languages` | JSONB | | | 语言能力 |
| `total_experience_years` | INTEGER | | | 总经验年数 |
| `sector_experience` | JSONB | | | 行业经验 |
| `region_experience` | JSONB | | | 地区经验 |
| `project_history` | JSONB | | | 项目历史 |
| `adb_project_count` | INTEGER | NOT NULL | `0` | ADB 项目数 |
| `wb_project_count` | INTEGER | NOT NULL | `0` | WB 项目数 |
| `total_project_value` | FLOAT | | | 项目总金额 USD |
| `cv_summary` | TEXT | | | 简历摘要 |
| `cv_full_text` | TEXT | | | 简历全文 |
| `cv_file_path` | VARCHAR(500) | | | 简历文件路径 |
| `cv_embedding` | VECTOR(1024) | | | 简历嵌入向量 |
| `skills_embedding` | VECTOR(1024) | | | 技能嵌入向量 |
| `internal_rating` | FLOAT | | | 内部评分 1-5 |
| `availability_score` | FLOAT | NOT NULL | `1.0` | 可用性 |
| `status` | VARCHAR(50) | NOT NULL, INDEX | `'active'` | active/on_project/unavailable/archived |
| `current_project_id` | UUID | FK → projects(id) SET NULL | | 当前项目 |
| `available_from` | DATE | | | 可用日期 |
| `tags` | VARCHAR[] | | | 标签数组 |
| `notes` | TEXT | | | 备注 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | |

**索引**:
- `idx_expert_cv_embedding USING hnsw (cv_embedding vector_cosine_ops) WITH (m=16, ef_construction=64)`
- `idx_expert_skills_embedding USING hnsw (skills_embedding vector_cosine_ops) WITH (m=16, ef_construction=64)`

#### `skill_tags` — 技能标签表

| 列名 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PK | `uuid_generate_v4()` | |
| `name` | VARCHAR(200) | NOT NULL, UNIQUE | | 技能名 |
| `name_en` | VARCHAR(200) | | | 英文名 |
| `category` | VARCHAR(100) | | | 分类 |
| `description` | TEXT | | | 描述 |
| `embedding` | VECTOR(1024) | | | 技能嵌入向量 |

#### `expert_skills` — 专家-技能关联表

| 列名 | 类型 | 约束 | 默认值 |
|------|------|------|--------|
| `expert_id` | UUID | PK, FK → experts(id) CASCADE | |
| `skill_id` | UUID | PK, FK → skill_tags(id) CASCADE | |
| `proficiency_level` | INTEGER | NOT NULL | `3` |
| `years_experience` | INTEGER | | |

#### `team_assignments` — 团队分配表

| 列名 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PK | `uuid_generate_v4()` | |
| `project_id` | UUID | FK → projects(id) CASCADE, NOT NULL, INDEX | | |
| `expert_id` | UUID | FK → experts(id) CASCADE, NOT NULL, INDEX | | |
| `role` | VARCHAR(100) | NOT NULL | | 角色 |
| `role_type` | VARCHAR(50) | | | key_expert/non_key_expert |
| `position` | VARCHAR(200) | | | 职位 |
| `responsibilities` | TEXT | | | 职责 |
| `person_months` | FLOAT | | | 人月 |
| `start_date` | DATE | | | |
| `end_date` | DATE | | | |
| `is_home_based` | BOOLEAN | NOT NULL | `false` | 是否为家庭办公 |
| `location` | VARCHAR(200) | | | |
| `match_score` | FLOAT | | | AI 匹配分 |
| `match_reasons` | JSONB | | | 匹配原因 |
| `status` | VARCHAR(50) | NOT NULL | `'proposed'` | proposed/confirmed/completed |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | |

#### `expert_match_results` — 专家匹配结果缓存表

| 列名 | 类型 | 约束 | 默认值 |
|------|------|------|--------|
| `id` | UUID | PK | `uuid_generate_v4()` |
| `project_id` | UUID | FK → projects(id) CASCADE, NOT NULL, INDEX | |
| `requirements_snapshot` | JSONB | | |
| `matched_experts` | JSONB | | |
| `team_composition` | JSONB | | |
| `algorithm_version` | VARCHAR(50) | | |
| `matching_criteria` | JSONB | | |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` |

---

### 3.9 预算管理

#### `unit_price_items` — 单价项目表

| 列名 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PK | `uuid_generate_v4()` | |
| `organization_id` | UUID | FK → users(id) CASCADE, NOT NULL, INDEX | | |
| `name` | VARCHAR(300) | NOT NULL, INDEX | | 项目名 |
| `name_en` | VARCHAR(300) | | | |
| `description` | TEXT | | | |
| `category` | VARCHAR(50) | NOT NULL, INDEX | `'other'` | remuneration/reimbursable/... |
| `unit` | VARCHAR(50) | | | 人月/台/次 |
| `unit_price` | FLOAT | NOT NULL | | 单价 |
| `currency` | VARCHAR(10) | NOT NULL | `'USD'` | |
| `min_price` | FLOAT | | | |
| `max_price` | FLOAT | | | |
| `source` | VARCHAR(200) | | | 来源 |
| `effective_date` | TIMESTAMPTZ | | | 生效日期 |
| `expiry_date` | TIMESTAMPTZ | | | 过期日期 |
| `applicable_regions` | VARCHAR[] | | | |
| `applicable_sectors` | VARCHAR[] | | | |
| `applicable_institutions` | VARCHAR[] | | | |
| `tags` | VARCHAR[] | | | |
| `notes` | TEXT | | | |
| `is_active` | BOOLEAN | NOT NULL | `true` | |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | |

#### `expert_rates` — 专家费率表

| 列名 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PK | `uuid_generate_v4()` | |
| `organization_id` | UUID | FK → users(id) CASCADE, NOT NULL | | |
| `level` | VARCHAR(100) | NOT NULL | | 级别 |
| `level_en` | VARCHAR(100) | | | |
| `description` | TEXT | | | |
| `monthly_rate` | FLOAT | NOT NULL | | 月费率 |
| `daily_rate` | FLOAT | | | |
| `hourly_rate` | FLOAT | | | |
| `currency` | VARCHAR(10) | NOT NULL | `'USD'` | |
| `min_rate` | FLOAT | | | |
| `max_rate` | FLOAT | | | |
| `years_experience_min` | INTEGER | | | |
| `years_experience_max` | INTEGER | | | |
| `applicable_positions` | VARCHAR[] | | | |
| `applicable_institutions` | VARCHAR[] | | | |
| `effective_date` | TIMESTAMPTZ | | | |
| `is_active` | BOOLEAN | NOT NULL | `true` | |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | |

#### `project_budgets` — 项目预算表

| 列名 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PK | `uuid_generate_v4()` | |
| `project_id` | UUID | FK → projects(id) CASCADE, NOT NULL, INDEX | | |
| `version` | INTEGER | NOT NULL | `1` | 版本号 |
| `status` | VARCHAR(50) | NOT NULL | `'draft'` | draft/approved/submitted |
| `total_amount` | FLOAT | | | 总金额 |
| `currency` | VARCHAR(10) | NOT NULL | `'USD'` | |
| `remuneration_total` | FLOAT | NOT NULL | `0` | 人员费用 |
| `reimbursable_total` | FLOAT | NOT NULL | `0` | 可报销费用 |
| `equipment_total` | FLOAT | NOT NULL | `0` | 设备费用 |
| `subcontract_total` | FLOAT | NOT NULL | `0` | 分包费用 |
| `contingency_total` | FLOAT | NOT NULL | `0` | 预备费 |
| `overhead_total` | FLOAT | NOT NULL | `0` | 管理费 |
| `budget_items` | JSONB | | | 明细 |
| `estimation_basis` | JSONB | | | 估算依据 |
| `assumptions` | JSONB | | | 假设条件 |
| `ai_suggestions` | JSONB | | | AI 建议 |
| `ai_warnings` | JSONB | | | AI 警告 |
| `notes` | TEXT | | | |
| `created_by` | UUID | FK → users(id) SET NULL | | |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | |

#### `budget_items` — 预算明细项表

| 列名 | 类型 | 约束 | 默认值 |
|------|------|------|--------|
| `id` | UUID | PK | `uuid_generate_v4()` |
| `budget_id` | UUID | FK → project_budgets(id) CASCADE, NOT NULL, INDEX | |
| `category` | VARCHAR(50) | NOT NULL | |
| `name` | VARCHAR(300) | NOT NULL | |
| `description` | TEXT | | |
| `unit` | VARCHAR(50) | | |
| `quantity` | FLOAT | NOT NULL | `1` |
| `unit_price` | FLOAT | NOT NULL | |
| `amount` | FLOAT | NOT NULL | |
| `currency` | VARCHAR(10) | NOT NULL | `'USD'` |
| `unit_price_item_id` | UUID | FK → unit_price_items(id) SET NULL | |
| `expert_id` | UUID | FK → experts(id) SET NULL | |
| `notes` | TEXT | | |
| `sort_order` | INTEGER | NOT NULL | `0` |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` |

---

### 3.10 支付与积分

#### `recharge_packages` — 充值套餐表

| 列名 | 类型 | 约束 | 默认值 |
|------|------|------|--------|
| `id` | UUID | PK | `uuid_generate_v4()` |
| `name` | VARCHAR(100) | NOT NULL | |
| `description` | TEXT | | |
| `credit_amount` | INTEGER | NOT NULL | |
| `price` | NUMERIC(10,2) | NOT NULL | |
| `currency` | VARCHAR(3) | NOT NULL | `'CNY'` |
| `is_active` | BOOLEAN | NOT NULL | `true` |
| `sort_order` | INTEGER | NOT NULL | `0` |
| `bonus_credits` | INTEGER | NOT NULL | `0` |
| `bonus_description` | VARCHAR(200) | | |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` |

#### `subscription_plans` — 订阅套餐表

| 列名 | 类型 | 约束 | 默认值 |
|------|------|------|--------|
| `id` | UUID | PK | `uuid_generate_v4()` |
| `name` | VARCHAR(100) | NOT NULL | |
| `description` | TEXT | | |
| `plan_type` | VARCHAR(50) | | |
| `monthly_credit_limit` | INTEGER | NOT NULL | `0` |
| `analysis_limit` | INTEGER | NOT NULL | `0` |
| `price` | NUMERIC(10,2) | NOT NULL | |
| `currency` | VARCHAR(3) | NOT NULL | `'CNY'` |
| `is_active` | BOOLEAN | NOT NULL | `true` |
| `is_popular` | BOOLEAN | NOT NULL | `false` |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` |

#### `payment_orders` — 支付订单表

| 列名 | 类型 | 约束 | 默认值 |
|------|------|------|--------|
| `id` | UUID | PK | `uuid_generate_v4()` |
| `order_no` | VARCHAR(64) | UNIQUE, NOT NULL, INDEX | |
| `user_id` | UUID | FK → users(id) CASCADE, NOT NULL, INDEX | |
| `amount` | NUMERIC(10,2) | NOT NULL | |
| `currency` | VARCHAR(3) | NOT NULL | `'CNY'` |
| `payment_method` | payment_method | NOT NULL | |
| `status` | payment_status | NOT NULL | `'pending'` |
| `product_type` | product_type | NOT NULL | |
| `product_id` | UUID | | |
| `gateway_order_no` | VARCHAR(128) | | |
| `gateway_response` | JSONB | | |
| `paid_at` | TIMESTAMPTZ | | |
| `closed_at` | TIMESTAMPTZ | | |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` |

#### `payment_transactions` — 支付流水表

| 列名 | 类型 | 约束 | 默认值 |
|------|------|------|--------|
| `id` | UUID | PK | `uuid_generate_v4()` |
| `user_id` | UUID | FK → users(id) CASCADE, NOT NULL, INDEX | |
| `payment_order_id` | UUID | FK → payment_orders(id) SET NULL | |
| `type` | transaction_type | NOT NULL | |
| `amount` | NUMERIC(10,2) | NOT NULL | |
| `balance_before` | NUMERIC(12,2) | NOT NULL | |
| `balance_after` | NUMERIC(12,2) | NOT NULL | |
| `description` | VARCHAR(500) | | |
| `related_type` | VARCHAR(50) | | |
| `related_id` | UUID | | |
| `created_at` | TIMESTAMPTZ | NOT NULL, INDEX | `now()` |

#### `user_subscriptions` — 用户订阅表

| 列名 | 类型 | 约束 | 默认值 |
|------|------|------|--------|
| `id` | UUID | PK | `uuid_generate_v4()` |
| `user_id` | UUID | FK → users(id) CASCADE, NOT NULL, UNIQUE | |
| `plan_id` | UUID | FK → subscription_plans(id), NOT NULL | |
| `status` | VARCHAR(20) | NOT NULL | `'active'` |
| `started_at` | TIMESTAMPTZ | | |
| `expires_at` | TIMESTAMPTZ | | |
| `cancelled_at` | TIMESTAMPTZ | | |
| `credits_used_this_month` | INTEGER | NOT NULL | `0` |
| `analyses_used_this_month` | INTEGER | NOT NULL | `0` |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` |

---

### 3.11 系统运营

#### `saved_searches` — 用户保存的搜索条件

| 列名 | 类型 | 约束 | 默认值 |
|------|------|------|--------|
| `id` | UUID | PK | `uuid_generate_v4()` |
| `user_id` | UUID | FK → users(id) CASCADE, NOT NULL, INDEX | |
| `name` | VARCHAR(200) | NOT NULL | |
| `filters` | JSONB | NOT NULL | `'{}'` |
| `is_default` | BOOLEAN | NOT NULL | `false` |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` |

**索引**: `idx_ss_user_default (user_id, is_default)`

#### `daily_stats` — 每日统计表

| 列名 | 类型 | 约束 | 默认值 |
|------|------|------|--------|
| `id` | UUID | PK | `uuid_generate_v4()` |
| `stat_date` | DATE | NOT NULL | |
| `metric_type` | VARCHAR(50) | NOT NULL | |
| `metric_value` | FLOAT | NOT NULL | `0` |
| `metric_count` | INTEGER | NOT NULL | `0` |
| `dimension` | VARCHAR(50) | | |
| `dimension_value` | VARCHAR(100) | | |
| `metadata` | JSONB | | |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` |

**索引**: `idx_ds_date_metric (stat_date, metric_type)`, `idx_ds_dimension (dimension, dimension_value)`

#### `usage_logs` — 使用日志表

| 列名 | 类型 | 约束 | 默认值 |
|------|------|------|--------|
| `id` | UUID | PK | `uuid_generate_v4()` |
| `user_id` | UUID | FK → users(id) CASCADE, NOT NULL, INDEX | |
| `action_type` | action_type | NOT NULL | |
| `resource_type` | VARCHAR(50) | | |
| `resource_id` | UUID | | |
| `credits_consumed` | INTEGER | NOT NULL | `0` |
| `tokens_consumed` | INTEGER | NOT NULL | `0` |
| `ip_address` | VARCHAR(45) | | |
| `user_agent` | VARCHAR(500) | | |
| `metadata` | JSONB | | |
| `created_at` | TIMESTAMPTZ | NOT NULL, INDEX | `now()` |

#### `system_metrics` — 系统指标表

| 列名 | 类型 | 约束 | 默认值 |
|------|------|------|--------|
| `id` | UUID | PK | `uuid_generate_v4()` |
| `timestamp` | TIMESTAMPTZ | NOT NULL, INDEX | `now()` |
| `category` | VARCHAR(50) | NOT NULL | |
| `metric_name` | VARCHAR(100) | NOT NULL | |
| `metric_value` | FLOAT | | |
| `metric_unit` | VARCHAR(20) | | |
| `labels` | JSONB | | |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` |

**索引**: `idx_sm_category_name (category, metric_name)`

---

## 4. ER 图

```
users ─────┬───< projects ─────┬───< bid_documents ───< bid_document_sections
           │                   │                   └───< bid_document_chunks
           │                   ├───< project_documents ───< project_document_chunks
           │                   ├────── bid_analyses (1:1)
           │                   ├────── bid_plans (1:1) ───< bid_plan_tasks
           │                   ├────── bid_predictions
           │                   ├───< team_assignments >─── experts
           │                   ├───< project_budgets ───< budget_items
           │                   └───< expert_match_results
           │
           ├───< experts ────< expert_skills >─── skill_tags
           ├───< unit_price_items
           ├───< expert_rates
           ├───< payment_orders ───< payment_transactions
           ├───< user_subscriptions ─── subscription_plans
           ├───< usage_logs
           └───< saved_searches

opportunities (独立，通过 projects.opportunity_id 关联)

knowledge_bases ───< knowledge_documents ───< knowledge_chunks

recharge_packages (独立配置表)
subscription_plans (独立配置表)
daily_stats (独立统计表)
system_metrics (独立指标表)
translation_cache (独立缓存表)
```

---

## 5. 通用触发器

```sql
-- 自动更新 updated_at 时间戳
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 应用到所有含 updated_at 列的表
CREATE TRIGGER set_updated_at BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
-- ... 对其他表重复 ...

-- 投标计划任务统计触发器
CREATE OR REPLACE FUNCTION update_bid_plan_stats()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE bid_plans SET
    total_tasks = (SELECT COUNT(*) FROM bid_plan_tasks WHERE plan_id = COALESCE(NEW.plan_id, OLD.plan_id)),
    completed_tasks = (SELECT COUNT(*) FROM bid_plan_tasks WHERE plan_id = COALESCE(NEW.plan_id, OLD.plan_id) AND status = 'completed')
  WHERE id = COALESCE(NEW.plan_id, OLD.plan_id);
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_bid_plan_tasks_stats
  AFTER INSERT OR UPDATE OR DELETE ON bid_plan_tasks
  FOR EACH ROW EXECUTE FUNCTION update_bid_plan_stats();
```

---

## 6. 向量索引汇总

| 表 | 列 | 维度 | 索引类型 | 参数 |
|----|-----|------|---------|------|
| `bid_document_chunks` | `embedding` | 1024 | HNSW | m=16, ef_construction=64 |
| `project_document_chunks` | `embedding` | 1024 | HNSW | m=16, ef_construction=64 |
| `knowledge_chunks` | `embedding` | 1024 | HNSW | m=16, ef_construction=64 |
| `experts` | `cv_embedding` | 1024 | HNSW | m=16, ef_construction=64 |
| `experts` | `skills_embedding` | 1024 | HNSW | m=16, ef_construction=64 |
| `skill_tags` | `embedding` | 1024 | — | 数据量小，全表扫描 |

所有向量索引使用 `vector_cosine_ops` (余弦距离)。

---

## 7. V1 → V2 改进总结

| 问题 | V1 状态 | V2 方案 |
|------|--------|---------|
| PK 类型不一致 | UUID / String(36) 混用 | 统一 UUID |
| 两套 Opportunity 表 | opportunities + bid_opportunities | 合并为单一 opportunities |
| 向量维度混乱 | 1536 → 2048 → 1024 | 固定 1024 |
| ORM-SQL 不同步 | project_document_chunks.embedding 未映射 | ORM 与 DDL 同步 |
| 枚举类型混用 | PG ENUM + SQLAlchemy Enum + CHECK 约束 | 统一 PG 原生 ENUM |
| 手工 SQL 迁移 | 10 个 .sql 文件，编号冲突 | Alembic 版本化迁移 |
| 时间戳无时区 | DateTime (无时区) | TIMESTAMPTZ + `now()` |
| datetime.utcnow() 已弃用 | 大量使用 | `datetime.now(timezone.utc)` |
| is_active 用 Integer | `is_active: Integer = 1` | `is_active: Boolean = true` |
| metadata 与 Column 冲突 | ORM 列名 metadata | 重命名为 metadata (JSONB) 或 extra_data |
