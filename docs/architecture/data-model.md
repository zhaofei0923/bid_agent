# BidAgent 数据模型设计

## 1. 实体关系图 (ERD)

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     users       │       │    projects     │       │   documents     │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │───┐   │ id (PK)         │───┐   │ id (PK)         │
│ email           │   │   │ user_id (FK)    │   │   │ project_id (FK) │
│ password_hash   │   └──▶│ name            │   └──▶│ name            │
│ name            │       │ description     │       │ type            │
│ role            │       │ opp_id (FK)     │──┐    │ file_path       │
│ language        │       │ status          │  │    │ file_size       │
│ credits_balance │       │ created_at      │  │    │ parsed_content  │
│ created_at      │       │ updated_at      │  │    │ created_at      │
│ updated_at      │       └─────────────────┘  │    └─────────────────┘
└─────────────────┘                            │              │
        │                                      │              │
        │       ┌─────────────────┐            │              ▼
        │       │ bid_opportunities│◀──────────┘    ┌─────────────────┐
        │       ├─────────────────┤                 │   embeddings    │
        │       │ id (PK)         │                 ├─────────────────┤
        │       │ source          │                 │ id (PK)         │
        │       │ external_id     │                 │ document_id(FK) │
        │       │ title           │                 │ chunk_index     │
        │       │ description     │                 │ content         │
        │       │ organization    │                 │ vector          │
        │       │ deadline        │                 │ metadata        │
        │       │ budget_min      │                 │ created_at      │
        │       │ budget_max      │                 └─────────────────┘
        │       │ location        │
        │       │ sector          │       ┌─────────────────┐
        │       │ status          │       │ generated_docs  │
        │       │ raw_data        │       ├─────────────────┤
        │       │ created_at      │       │ id (PK)         │
        │       │ updated_at      │       │ project_id (FK) │
        │       └─────────────────┘       │ type            │
        │                                 │ title           │
        ▼                                 │ content         │
┌─────────────────┐                       │ version         │
│ credit_trans    │                       │ status          │
├─────────────────┤                       │ created_at      │
│ id (PK)         │                       └─────────────────┘
│ user_id (FK)    │
│ type            │       ┌─────────────────┐
│ amount          │       │  llm_usages     │
│ balance_after   │       ├─────────────────┤
│ reference_type  │       │ id (PK)         │
│ reference_id    │       │ user_id (FK)    │
│ description     │       │ project_id (FK) │
│ created_at      │       │ model           │
└─────────────────┘       │ prompt_tokens   │
                          │ completion_tkns │
                          │ credits_cost    │
                          │ request_type    │
                          │ created_at      │
                          └─────────────────┘
```

## 2. 表结构详细设计

### 2.1 users (用户表)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    company VARCHAR(200),
    phone VARCHAR(50),
    avatar_url VARCHAR(500),
    
    -- 角色与权限
    role VARCHAR(20) NOT NULL DEFAULT 'user',  -- user, admin, super_admin
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    
    -- 偏好设置
    language VARCHAR(10) NOT NULL DEFAULT 'zh',  -- zh, en, fr
    timezone VARCHAR(50) DEFAULT 'Asia/Shanghai',
    
    -- 积分
    credits_balance INTEGER NOT NULL DEFAULT 0,
    
    -- 时间戳
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role) WHERE is_active = true;
```

### 2.2 bid_opportunities (招标机会表)

```sql
CREATE TABLE bid_opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 来源标识
    source VARCHAR(20) NOT NULL,  -- adb, wb, un
    external_id VARCHAR(100) NOT NULL,  -- 原网站ID
    url VARCHAR(500) NOT NULL,
    
    -- 基本信息
    title VARCHAR(500) NOT NULL,
    description TEXT,
    organization VARCHAR(200),  -- 发布机构
    
    -- 时间与金额
    published_at TIMESTAMP WITH TIME ZONE,
    deadline TIMESTAMP WITH TIME ZONE,
    budget_min DECIMAL(15, 2),
    budget_max DECIMAL(15, 2),
    currency VARCHAR(10) DEFAULT 'USD',
    
    -- 分类信息
    location VARCHAR(200),  -- 项目地点
    country VARCHAR(100),
    sector VARCHAR(100),  -- 行业领域
    procurement_type VARCHAR(50),  -- 采购类型: cqs, qcbs, ics等
    
    -- 状态
    status VARCHAR(20) NOT NULL DEFAULT 'open',  -- open, closed, cancelled
    
    -- 原始数据 (JSON存储抓取的原始信息)
    raw_data JSONB,
    
    -- 全文搜索
    search_vector tsvector,
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT uq_source_external_id UNIQUE (source, external_id)
);

-- 索引
CREATE INDEX idx_opportunities_status_deadline ON bid_opportunities(status, deadline DESC) 
    WHERE status = 'open';
CREATE INDEX idx_opportunities_source ON bid_opportunities(source);
CREATE INDEX idx_opportunities_sector ON bid_opportunities(sector);
CREATE INDEX idx_opportunities_search ON bid_opportunities USING GIN(search_vector);

-- 全文搜索触发器
CREATE OR REPLACE FUNCTION update_opportunities_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.organization, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_opportunities_search_vector
    BEFORE INSERT OR UPDATE ON bid_opportunities
    FOR EACH ROW EXECUTE FUNCTION update_opportunities_search_vector();
```

### 2.3 projects (项目表)

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    opportunity_id UUID REFERENCES bid_opportunities(id) ON DELETE SET NULL,
    
    -- 基本信息
    name VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- 项目状态
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    -- draft: 草稿
    -- analyzing: 分析中
    -- generating: 生成中
    -- review: 待审核
    -- submitted: 已提交
    -- won: 中标
    -- lost: 未中标
    
    -- 投标配置
    config JSONB DEFAULT '{}',
    -- {
    --   "team_size": 3,
    --   "duration_months": 12,
    --   "approach": "technical_heavy"
    -- }
    
    -- 时间戳
    deadline TIMESTAMP WITH TIME ZONE,
    submitted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_projects_user ON projects(user_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_deadline ON projects(deadline) WHERE status NOT IN ('submitted', 'won', 'lost');
```

### 2.4 documents (文档表)

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- 文档信息
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    -- tor: 任务书
    -- rfp: 招标文件
    -- company_profile: 公司简介
    -- cv: 专家简历
    -- past_project: 历史项目
    -- reference: 参考资料
    -- other: 其他
    
    -- 文件存储
    file_path VARCHAR(500) NOT NULL,  -- S3/MinIO路径
    file_size INTEGER,
    mime_type VARCHAR(100),
    
    -- 解析内容
    parsed_content TEXT,  -- 提取的文本内容
    parse_status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, completed, failed
    parse_error TEXT,
    
    -- 元数据
    metadata JSONB DEFAULT '{}',
    -- {
    --   "page_count": 50,
    --   "language": "en",
    --   "extracted_deadline": "2026-03-01"
    -- }
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_documents_project ON documents(project_id);
CREATE INDEX idx_documents_type ON documents(type);
```

### 2.5 embeddings (向量嵌入表)

```sql
-- 需要先启用pgvector扩展
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- 分块信息
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    
    -- 向量 (1536维 for OpenAI, 可根据模型调整)
    vector vector(1536),
    
    -- 元数据
    metadata JSONB DEFAULT '{}',
    -- {
    --   "page_number": 5,
    --   "section": "technical_approach",
    --   "token_count": 500
    -- }
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 向量索引 (IVFFlat用于近似搜索)
CREATE INDEX idx_embeddings_vector ON embeddings 
    USING ivfflat (vector vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX idx_embeddings_document ON embeddings(document_id);
```

### 2.6 generated_docs (生成文档表)

```sql
CREATE TABLE generated_docs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- 文档类型
    type VARCHAR(50) NOT NULL,
    -- technical_proposal: 技术方案
    -- company_experience: 公司经验
    -- team_composition: 团队组成
    -- work_plan: 工作计划
    -- methodology: 方法论
    
    -- 内容
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    
    -- 版本控制
    version INTEGER NOT NULL DEFAULT 1,
    parent_id UUID REFERENCES generated_docs(id),
    
    -- 状态
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    -- draft, approved, exported
    
    -- 生成信息
    generation_config JSONB,  -- 使用的prompt、参数等
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_generated_docs_project ON generated_docs(project_id);
CREATE INDEX idx_generated_docs_type ON generated_docs(type);
```

### 2.7 credit_transactions (积分交易表)

```sql
CREATE TABLE credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 交易类型
    type VARCHAR(20) NOT NULL,
    -- recharge: 充值
    -- consume: 消费
    -- refund: 退款
    -- bonus: 赠送
    -- expire: 过期
    
    -- 金额
    amount INTEGER NOT NULL,  -- 正数增加，负数减少
    balance_after INTEGER NOT NULL,  -- 交易后余额
    
    -- 关联信息
    reference_type VARCHAR(50),  -- llm_usage, order, admin
    reference_id UUID,
    
    -- 描述
    description VARCHAR(500),
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- 按月分区
CREATE TABLE credit_transactions_2026_01 PARTITION OF credit_transactions
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE credit_transactions_2026_02 PARTITION OF credit_transactions
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
-- ... 继续创建后续月份分区

-- 索引
CREATE INDEX idx_credit_trans_user ON credit_transactions(user_id, created_at DESC);
CREATE INDEX idx_credit_trans_type ON credit_transactions(type);
```

### 2.8 llm_usages (LLM使用记录表)

```sql
CREATE TABLE llm_usages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    
    -- 模型信息
    model VARCHAR(50) NOT NULL,  -- deepseek-v3, deepseek-r1
    
    -- Token统计
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    total_tokens INTEGER GENERATED ALWAYS AS (prompt_tokens + completion_tokens) STORED,
    
    -- 费用
    credits_cost INTEGER NOT NULL,
    
    -- 请求信息
    request_type VARCHAR(50) NOT NULL,
    -- analysis: 文档分析
    -- generation: 内容生成
    -- qa: 问答
    -- embedding: 向量化
    
    -- 元数据
    metadata JSONB DEFAULT '{}',
    -- {
    --   "latency_ms": 1500,
    --   "cache_hit": false
    -- }
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_llm_usages_user ON llm_usages(user_id, created_at DESC);
CREATE INDEX idx_llm_usages_project ON llm_usages(project_id);
CREATE INDEX idx_llm_usages_model ON llm_usages(model);
```

### 2.9 recharge_orders (充值订单表)

```sql
CREATE TABLE recharge_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 订单信息
    order_no VARCHAR(50) NOT NULL UNIQUE,
    
    -- 套餐
    package_id VARCHAR(50) NOT NULL,
    credits_amount INTEGER NOT NULL,  -- 积分数量
    price DECIMAL(10, 2) NOT NULL,  -- 金额
    currency VARCHAR(10) NOT NULL DEFAULT 'CNY',
    
    -- 支付信息
    payment_method VARCHAR(20),  -- alipay, wechat, stripe
    payment_id VARCHAR(100),  -- 支付平台订单号
    
    -- 状态
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- pending, paid, cancelled, refunded
    
    -- 时间戳
    paid_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_orders_user ON recharge_orders(user_id);
CREATE INDEX idx_orders_status ON recharge_orders(status);
CREATE INDEX idx_orders_no ON recharge_orders(order_no);
```

## 3. 积分套餐配置

```sql
-- 套餐定义 (可放配置表或代码常量)
CREATE TABLE credit_packages (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    credits INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'CNY',
    bonus_credits INTEGER DEFAULT 0,  -- 赠送积分
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 预设套餐
INSERT INTO credit_packages (id, name, name_en, credits, price, bonus_credits, sort_order) VALUES
('starter', '入门包', 'Starter', 1000, 49.00, 0, 1),
('basic', '基础包', 'Basic', 5000, 199.00, 500, 2),
('pro', '专业包', 'Pro', 20000, 699.00, 3000, 3),
('enterprise', '企业包', 'Enterprise', 100000, 2999.00, 20000, 4);
```

## 4. 积分消费规则

```python
# config/credits.py

CREDIT_COSTS = {
    # 文档分析
    "document_analysis": {
        "base": 5,  # 基础费用
        "per_page": 1,  # 每页额外费用
    },
    
    # 内容生成
    "generation": {
        "technical_proposal": 50,
        "company_experience": 30,
        "team_composition": 20,
        "work_plan": 40,
        "methodology": 30,
    },
    
    # LLM调用 (per 1K tokens)
    "llm": {
        "deepseek-v3": {
            "input": 0.5,
            "output": 1.0,
        },
        "deepseek-r1": {
            "input": 2.0,
            "output": 4.0,
        },
    },
    
    # 其他功能
    "embedding": 0.1,  # per 1K tokens
    "export_pdf": 10,
}
```

## 5. 数据库迁移

### 5.1 Alembic配置

```python
# alembic/env.py
from app.models import Base
from app.config import settings

target_metadata = Base.metadata

def run_migrations_online():
    connectable = create_engine(settings.DATABASE_URL)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()
```

### 5.2 迁移命令

```bash
# 创建迁移
alembic revision --autogenerate -m "create initial tables"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

## 6. SQLAlchemy 模型示例

```python
# app/models/user.py
from sqlalchemy import Column, String, Boolean, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    company = Column(String(200))
    
    role = Column(String(20), nullable=False, default="user")
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    
    language = Column(String(10), nullable=False, default="zh")
    credits_balance = Column(Integer, nullable=False, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    credit_transactions = relationship("CreditTransaction", back_populates="user")
```

```python
# app/models/opportunity.py
from sqlalchemy import Column, String, Text, DateTime, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
from app.db.base import Base
import uuid

class BidOpportunity(Base):
    __tablename__ = "bid_opportunities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(20), nullable=False)
    external_id = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    
    title = Column(String(500), nullable=False)
    description = Column(Text)
    organization = Column(String(200))
    
    published_at = Column(DateTime(timezone=True))
    deadline = Column(DateTime(timezone=True))
    budget_min = Column(Numeric(15, 2))
    budget_max = Column(Numeric(15, 2))
    currency = Column(String(10), default="USD")
    
    location = Column(String(200))
    country = Column(String(100))
    sector = Column(String(100))
    procurement_type = Column(String(50))
    
    status = Column(String(20), nullable=False, default="open")
    raw_data = Column(JSONB)
    search_vector = Column(TSVECTOR)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_opp_source_external', 'source', 'external_id', unique=True),
        Index('idx_opp_status_deadline', 'status', 'deadline'),
    )
```

## 7. 向量检索示例

```python
# app/services/embedding_service.py
from sqlalchemy import text
from pgvector.sqlalchemy import Vector

async def similarity_search(
    db: AsyncSession,
    query_vector: list[float],
    project_id: str,
    limit: int = 5
) -> list[dict]:
    """
    基于向量相似度搜索相关文档片段
    """
    sql = text("""
        SELECT 
            e.id,
            e.content,
            e.metadata,
            d.name as document_name,
            1 - (e.vector <=> :query_vector) as similarity
        FROM embeddings e
        JOIN documents d ON e.document_id = d.id
        WHERE d.project_id = :project_id
        ORDER BY e.vector <=> :query_vector
        LIMIT :limit
    """)
    
    result = await db.execute(sql, {
        "query_vector": str(query_vector),
        "project_id": project_id,
        "limit": limit
    })
    
    return [dict(row) for row in result.fetchall()]
```

---

## 相关文档
- [系统架构](./system-overview.md)
- [Agent工作流](./agent-workflow.md)
- [API契约](../api-contracts/openapi.yaml)
