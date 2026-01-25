# 任务规格文档模板

> 本模板定义了 Mini-Agent 可解析的标准化任务文档格式。
> 所有 `docs/task-specs/` 下的任务文档应遵循此格式。

---

## 模板结构

每个任务文档由两部分组成：
1. **YAML Front Matter** - 机器可读的元信息
2. **Markdown 正文** - 人类可读的详细说明

---

## YAML Front Matter 规范

```yaml
---
# ============================================================
# 任务元信息 (必需字段)
# ============================================================

id: M1-03                    # 任务唯一标识，格式: M{里程碑}-{序号}
title: 注册接口               # 任务标题，简明扼要
executor: mini-agent         # 执行者: mini-agent | opus
priority: P0                 # 优先级: P0(阻塞) | P1(重要) | P2(一般)
estimated_hours: 2           # 预估工时(小时)
task_type: coding            # 任务类型，用于路由到子代理

# ============================================================
# 依赖与输出 (必需字段)
# ============================================================

dependencies:                # 前置依赖任务列表
  - M1-01
  - M1-02

outputs:                     # 输出文件路径列表
  - backend/app/schemas/auth.py
  - backend/app/services/auth_service.py
  - backend/app/api/v1/auth.py
  - backend/tests/api/test_auth.py

# ============================================================
# 验收标准 (必需字段)
# ============================================================

acceptance_criteria:         # 验收标准列表，每项对应一个 AC-N
  - POST /api/v1/auth/register 可用
  - 邮箱唯一性检查
  - 密码强度验证 (至少8位，包含大小写和数字)
  - 注册成功返回 JWT Token
  - 测试覆盖率 > 80%

---
```

### 字段详细说明

#### `id` (必需)
- **格式**: `M{X}-{YY}`，X 为里程碑编号(0-8)，YY 为两位序号(01-99)
- **示例**: `M0-01`, `M1-03`, `M5-12`

#### `executor` (必需)
- **可选值**:
  - `mini-agent`: 由 Mini-Agent CLI 自动执行
  - `opus`: 由 Opus 4.5 辅助设计，需人工参与

#### `priority` (必需)
- **可选值**:
  - `P0`: 阻塞其他任务，必须优先完成
  - `P1`: 重要但不阻塞
  - `P2`: 一般优先级

#### `task_type` (必需)
- **可选值及子代理映射**:

| task_type | 子代理 | 适用场景 |
|-----------|--------|---------|
| `coding` | Coder | 代码编写、API实现、组件开发 |
| `testing` | Tester | 单元测试、集成测试、E2E测试 |
| `documentation` | Documenter | 技术文档、API文档、README |
| `design` | Architect | 架构设计、数据模型设计 |
| `research` | Researcher | 技术调研、方案对比 |

#### `dependencies` (可选)
- 格式: 任务 ID 数组
- 为空时使用 `dependencies: []` 或省略

#### `outputs` (必需)
- 格式: 相对于项目根目录的文件路径数组
- 所有由该任务产出的文件

#### `acceptance_criteria` (必需)
- 格式: 验收标准描述数组
- 每项将在 Markdown 正文中展开为 `AC-N` 格式

---

## Markdown 正文规范

### 固定章节顺序

```markdown
## 描述
[一段简洁的任务描述，说明要做什么、为什么做]

## 输入
[前置条件、依赖的已有代码或文档]

## 输出文件
[文件路径列表，与 YAML 中的 outputs 对应]

## 验收标准
[详细的验收标准，AC-N 格式]

## 详细步骤
[Mini-Agent 执行的具体步骤]

## 代码模板
[关键代码框架或示例]
```

### 验收标准格式

使用 `AC-N:` 前缀，便于 Mini-Agent 追踪完成状态：

```markdown
## 验收标准

- [ ] AC-1: POST /api/v1/auth/register 返回 201 状态码
- [ ] AC-2: 重复邮箱注册返回 409 错误
- [ ] AC-3: 密码不符合强度要求返回 422 错误
- [ ] AC-4: 注册成功返回包含 access_token 和 refresh_token 的 JSON
- [ ] AC-5: 单元测试覆盖率 >= 80%
```

### 代码模板格式

提供关键代码框架，帮助 Mini-Agent 生成符合预期的代码：

````markdown
## 代码模板

### backend/app/schemas/auth.py
```python
from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=2, max_length=100)

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
```

### backend/app/api/v1/auth.py
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["认证"])

@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    # 实现注册逻辑
    pass
```
````

---

## 完整任务文档示例

```markdown
---
id: M1-03
title: 注册接口
executor: mini-agent
priority: P0
estimated_hours: 2
task_type: coding
dependencies:
  - M1-01
  - M1-02
outputs:
  - backend/app/schemas/auth.py
  - backend/app/services/auth_service.py
  - backend/app/api/v1/auth.py
  - backend/tests/api/test_auth.py
acceptance_criteria:
  - POST /api/v1/auth/register 可用
  - 邮箱唯一性检查
  - 密码强度验证
  - 注册成功返回 JWT Token
  - 测试覆盖率 > 80%
---

## 描述

实现用户注册 API，允许新用户通过邮箱和密码创建账户。注册成功后返回 JWT Token，
用户可直接进入已登录状态。

## 输入

- 已完成的 User 数据模型 (M1-01)
- 已实现的 JWT 认证服务 (M1-02)
- API 契约定义: `docs/api-contracts/openapi.yaml`

## 输出文件

```
backend/
├── app/
│   ├── schemas/
│   │   └── auth.py          # 认证相关 Schema
│   ├── services/
│   │   └── auth_service.py  # 认证业务逻辑
│   └── api/v1/
│       └── auth.py          # 认证路由
└── tests/
    └── api/
        └── test_auth.py     # 认证接口测试
```

## 验收标准

- [ ] AC-1: POST /api/v1/auth/register 返回 201 状态码
- [ ] AC-2: 邮箱已存在时返回 409 Conflict 错误
- [ ] AC-3: 密码少于8位或缺少大小写/数字时返回 422 错误
- [ ] AC-4: 响应包含 `access_token`, `refresh_token`, `user` 字段
- [ ] AC-5: 密码以 bcrypt 哈希存储，不存储明文
- [ ] AC-6: 单元测试覆盖率 >= 80%

## 详细步骤

1. **创建 Schema 定义** (`schemas/auth.py`)
   - RegisterRequest: email, password, name
   - AuthResponse: access_token, refresh_token, token_type, user
   - 添加 Pydantic 验证器

2. **实现认证服务** (`services/auth_service.py`)
   - `register_user()`: 检查邮箱、哈希密码、创建用户、生成 Token
   - `validate_password_strength()`: 验证密码强度

3. **创建 API 路由** (`api/v1/auth.py`)
   - POST /auth/register 端点
   - 错误处理和响应格式化

4. **编写单元测试** (`tests/api/test_auth.py`)
   - 正常注册流程
   - 重复邮箱测试
   - 密码强度测试
   - 字段验证测试

## 代码模板

### backend/app/schemas/auth.py
```python
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=2, max_length=100)
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r'[A-Z]', v):
            raise ValueError('密码必须包含大写字母')
        if not re.search(r'[a-z]', v):
            raise ValueError('密码必须包含小写字母')
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含数字')
        return v

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    
    model_config = {"from_attributes": True}

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
```

### backend/app/services/auth_service.py
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.security import get_password_hash, create_access_token, create_refresh_token
from app.schemas.auth import RegisterRequest, AuthResponse

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def register_user(self, data: RegisterRequest) -> AuthResponse:
        # 检查邮箱是否已存在
        existing = await self.db.execute(
            select(User).where(User.email == data.email)
        )
        if existing.scalar_one_or_none():
            raise EmailAlreadyExistsError(data.email)
        
        # 创建用户
        user = User(
            email=data.email,
            password_hash=get_password_hash(data.password),
            name=data.name,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        # 生成 Token
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user,
        )
```

---

## 依赖
- M1-01: 用户数据模型
- M1-02: JWT 认证服务
```

---

## 里程碑文档结构

每个里程碑的 `README.md` 应包含：

```markdown
# M{X} - {里程碑名称} 任务规格书

## 概述
| 属性 | 值 |
|------|-----|
| 里程碑 | M{X} - {名称} |
| 周期 | Week {N} |
| 任务总数 | {N} |
| Mini-Agent 任务 | {N} |
| Opus 任务 | {N} |

## 目标
- 目标 1
- 目标 2

---

## 任务列表

### M{X}-01: {任务名称}
[按本模板格式定义每个任务]

---

### M{X}-02: {任务名称}
[...]

---

## 里程碑检查点

### 完成标准
- [ ] 标准 1
- [ ] 标准 2

### 交付物
1. 交付物 1
2. 交付物 2
```

---

## 使用说明

### 1. 使用 Opus 4.5 生成任务文档

在 Copilot Chat 中：
```
请按照 docs/task-spec-template.md 格式，为以下功能编写任务规格文档：

[功能描述]

技术约束：
- 后端: FastAPI + SQLAlchemy 2.x
- 前端: Next.js 15 + TypeScript
- 参考: docs/architecture/data-model.md
```

### 2. Mini-Agent 解析执行

```bash
# Mini-Agent 读取文档并执行
mini-agent run docs/task-specs/M1-user-system/README.md --task M1-03

# Mini-Agent 会：
# 1. 解析 YAML Front Matter 获取元信息
# 2. 检查 dependencies 中的任务是否完成
# 3. 根据 task_type 路由到对应子代理
# 4. 按 "详细步骤" 章节执行
# 5. 生成 outputs 中定义的文件
# 6. 验证 acceptance_criteria 是否满足
```

### 3. 更新任务状态

完成任务后，更新验收标准的 checkbox：

```markdown
## 验收标准

- [x] AC-1: POST /api/v1/auth/register 返回 201 状态码
- [x] AC-2: 邮箱已存在时返回 409 Conflict 错误
- [x] AC-3: 密码强度验证
- [x] AC-4: 响应包含正确字段
- [x] AC-5: 密码哈希存储
- [x] AC-6: 测试覆盖率 >= 80%
```

---

> 📝 **文档版本**: 1.0 | **更新日期**: 2026-01-25
