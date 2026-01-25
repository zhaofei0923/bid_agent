# M1 - 用户系统任务规格书

## 概述

| 属性 | 值 |
|------|-----|
| 里程碑 | M1 - User System |
| 周期 | Week 2 |
| 任务总数 | 10 |
| Mini-Agent 任务 | 8 |
| Opus 任务 | 2 |

## 目标

- 实现用户注册、登录、认证
- 建立JWT认证机制
- 实现基本权限控制

---

## 任务列表

---

### M1-01: 用户数据模型设计

```yaml
---
id: M1-01
title: 用户数据模型设计
executor: opus
priority: P0
estimated_hours: 2
task_type: design
dependencies:
  - M0-06
outputs:
  - backend/app/models/user.py
  - backend/alembic/versions/001_create_users.py
acceptance_criteria:
  - User模型定义完整
  - 密码加密策略确定（bcrypt）
  - 索引设计合理（email唯一索引）
  - 迁移脚本可执行
---
```

#### 描述

设计用户相关数据模型，包括用户表、会话管理。

#### 输入

- 数据库迁移配置 (M0-06)

#### 输出文件

```
backend/app/
├── models/
│   └── user.py
└── alembic/versions/
    └── 001_create_users.py
```

#### 验收标准

- [ ] AC-1: User模型定义完整（含所有必要字段）
- [ ] AC-2: 密码加密策略确定（bcrypt）
- [ ] AC-3: 索引设计合理（email唯一索引）
- [ ] AC-4: 迁移脚本可执行

#### 代码模板

**app/models/user.py**
```python
from sqlalchemy import Column, String, Boolean, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    company = Column(String(200))
    phone = Column(String(50))
    avatar_url = Column(String(500))
    
    # 角色与权限
    role = Column(String(20), nullable=False, default="user")
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    
    # 偏好设置
    language = Column(String(10), nullable=False, default="zh")
    timezone = Column(String(50), default="Asia/Shanghai")
    
    # 积分
    credits_balance = Column(Integer, nullable=False, default=0)
    
    # 时间戳
    last_login_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

---

### M1-02: 认证服务核心

```yaml
---
id: M1-02
title: 认证服务核心
executor: opus
priority: P0
estimated_hours: 3
task_type: design
dependencies:
  - M1-01
outputs:
  - backend/app/core/security.py
  - backend/app/core/auth.py
acceptance_criteria:
  - JWT生成与验证正确
  - Refresh Token机制实现
  - Token黑名单（登出）支持
  - 密码加密与验证正确
---
```

#### 描述

实现JWT认证核心逻辑，包括Token生成、验证、刷新。

#### 输入

- 用户数据模型 (M1-01)

#### 输出文件

```
backend/app/core/
├── security.py
└── auth.py
```

#### 验收标准

- [ ] AC-1: JWT生成与验证正确
- [ ] AC-2: Refresh Token机制实现
- [ ] AC-3: Token黑名单（登出）支持
- [ ] AC-4: 密码加密与验证正确

#### 代码模板

**app/core/security.py**
```python
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        return None
```

**app/core/auth.py**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user_id = payload.get("sub")
    user = await db.get(User, user_id)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(allowed_roles: list[str]):
    async def role_checker(user: User = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        return user
    return role_checker
```

---

### M1-03: 注册接口

```yaml
---
id: M1-03
title: 注册接口
executor: mini-agent
priority: P0
estimated_hours: 2
task_type: coding
dependencies:
  - M1-02
outputs:
  - backend/app/schemas/auth.py
  - backend/app/services/auth_service.py
  - backend/app/api/v1/auth.py
  - backend/tests/api/test_auth.py
acceptance_criteria:
  - POST /api/v1/auth/register 可用
  - 邮箱唯一性检查
  - 密码强度验证（最少8位）
  - 返回JWT Token
  - 测试覆盖率 > 80%
---
```

#### 描述

实现用户注册API。

#### 输入

- 认证服务核心 (M1-02)

#### 输出文件

```
backend/app/
├── schemas/
│   └── auth.py
├── services/
│   └── auth_service.py
├── api/v1/
│   └── auth.py
└── tests/api/
    └── test_auth.py
```

#### 验收标准

- [ ] AC-1: POST /api/v1/auth/register 可用
- [ ] AC-2: 邮箱唯一性检查
- [ ] AC-3: 密码强度验证（最少8位）
- [ ] AC-4: 返回JWT Token
- [ ] AC-5: 测试覆盖率 > 80%

#### 详细步骤

1. 创建注册Schema
2. 实现注册Service
3. 创建注册路由
4. 添加邮箱验证（可选）
5. 编写单元测试

#### 代码模板

**app/schemas/auth.py**
```python
from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=2, max_length=100)
    company: str | None = None
    language: str = "zh"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    company: str | None
    role: str
    language: str
    credits_balance: int
    
    class Config:
        from_attributes = True
```

---

### M1-04: 登录接口

```yaml
---
id: M1-04
title: 登录接口
executor: mini-agent
priority: P0
estimated_hours: 2
task_type: coding
dependencies:
  - M1-02
outputs:
  - backend/app/api/v1/auth.py
  - backend/tests/api/test_auth.py
acceptance_criteria:
  - POST /api/v1/auth/login 可用
  - 凭证验证正确
  - 登录失败计数（防暴力破解）
  - 更新last_login_at
  - 返回JWT Token
---
```

#### 描述

实现用户登录API。

#### 输入

- 认证服务核心 (M1-02)

#### 输出文件

- `backend/app/api/v1/auth.py` (追加)
- `backend/tests/api/test_auth.py` (追加)

#### 验收标准

- [ ] AC-1: POST /api/v1/auth/login 可用
- [ ] AC-2: 凭证验证正确
- [ ] AC-3: 登录失败计数（防暴力破解）
- [ ] AC-4: 更新last_login_at
- [ ] AC-5: 返回JWT Token

---

### M1-05: Token刷新接口

```yaml
---
id: M1-05
title: Token刷新接口
executor: mini-agent
priority: P0
estimated_hours: 1
task_type: coding
dependencies:
  - M1-02
outputs:
  - backend/app/api/v1/auth.py
acceptance_criteria:
  - POST /api/v1/auth/refresh 可用
  - 验证refresh_token有效性
  - 返回新的access_token
  - refresh_token单次使用（可选）
---
```

#### 描述

实现Token刷新API。

#### 输入

- 认证服务核心 (M1-02)

#### 输出文件

- `backend/app/api/v1/auth.py` (追加)

#### 验收标准

- [ ] AC-1: POST /api/v1/auth/refresh 可用
- [ ] AC-2: 验证refresh_token有效性
- [ ] AC-3: 返回新的access_token
- [ ] AC-4: refresh_token单次使用（可选）

---

### M1-06: 登出接口

```yaml
---
id: M1-06
title: 登出接口
executor: mini-agent
priority: P1
estimated_hours: 1
task_type: coding
dependencies:
  - M1-02
  - M0-04
outputs:
  - backend/app/core/token_blacklist.py
  - backend/app/api/v1/auth.py
acceptance_criteria:
  - POST /api/v1/auth/logout 可用
  - Token加入Redis黑名单
  - 后续请求拒绝该Token
---
```

#### 描述

实现用户登出API，Token加入黑名单。

#### 输入

- 认证服务核心 (M1-02)
- Docker环境 (M0-04) - Redis

#### 输出文件

```
backend/app/
├── core/
│   └── token_blacklist.py
└── api/v1/
    └── auth.py (追加)
```

#### 验收标准

- [ ] AC-1: POST /api/v1/auth/logout 可用
- [ ] AC-2: Token加入Redis黑名单
- [ ] AC-3: 后续请求拒绝该Token

#### 代码模板

**app/core/token_blacklist.py**
```python
from app.core.redis import redis_client
from app.config import settings

async def blacklist_token(token: str, expires_in: int):
    """将Token加入黑名单"""
    await redis_client.setex(
        f"blacklist:{token}",
        expires_in,
        "1"
    )

async def is_token_blacklisted(token: str) -> bool:
    """检查Token是否在黑名单"""
    return await redis_client.exists(f"blacklist:{token}")
```

---

### M1-07: 密码重置流程

```yaml
---
id: M1-07
title: 密码重置流程
executor: mini-agent
priority: P1
estimated_hours: 3
task_type: coding
dependencies:
  - M1-03
outputs:
  - backend/app/api/v1/auth.py
  - backend/app/services/email_service.py
acceptance_criteria:
  - POST /api/v1/auth/password/forgot 发送重置邮件
  - POST /api/v1/auth/password/reset 重置密码
  - 重置Token有效期24小时
  - 使用后Token失效
---
```

#### 描述

实现忘记密码和重置密码功能。

#### 输入

- 注册接口 (M1-03)
- 邮件服务

#### 输出文件

- `backend/app/api/v1/auth.py` (追加)
- `backend/app/services/email_service.py`

#### 验收标准

- [ ] AC-1: POST /api/v1/auth/password/forgot 发送重置邮件
- [ ] AC-2: POST /api/v1/auth/password/reset 重置密码
- [ ] AC-3: 重置Token有效期24小时
- [ ] AC-4: 使用后Token失效

---

### M1-08: 用户信息接口

```yaml
---
id: M1-08
title: 用户信息接口
executor: mini-agent
priority: P1
estimated_hours: 2
task_type: coding
dependencies:
  - M1-02
outputs:
  - backend/app/api/v1/users.py
  - backend/app/schemas/user.py
  - backend/tests/api/test_users.py
acceptance_criteria:
  - GET /api/v1/users/me 返回当前用户
  - PATCH /api/v1/users/me 更新用户信息
  - PUT /api/v1/users/me/password 修改密码
  - 敏感字段脱敏
---
```

#### 描述

实现获取和更新当前用户信息API。

#### 输入

- 认证服务核心 (M1-02)

#### 输出文件

```
backend/app/
├── api/v1/
│   └── users.py
├── schemas/
│   └── user.py
└── tests/api/
    └── test_users.py
```

#### 验收标准

- [ ] AC-1: GET /api/v1/users/me 返回当前用户
- [ ] AC-2: PATCH /api/v1/users/me 更新用户信息
- [ ] AC-3: PUT /api/v1/users/me/password 修改密码
- [ ] AC-4: 敏感字段脱敏

---

### M1-09: 前端认证状态管理

```yaml
---
id: M1-09
title: 前端认证状态管理
executor: mini-agent
priority: P0
estimated_hours: 3
task_type: coding
dependencies:
  - M0-03
  - M0-07
outputs:
  - frontend/src/stores/auth-store.ts
  - frontend/src/lib/api/auth.ts
  - frontend/src/hooks/use-auth.ts
acceptance_criteria:
  - Zustand auth store实现
  - Token存储（httpOnly cookie或localStorage）
  - 自动刷新Token
  - 401自动跳转登录
---
```

#### 描述

实现前端认证状态管理和Token存储。

#### 输入

- 前端项目骨架 (M0-03)
- shadcn/ui组件库 (M0-07)

#### 输出文件

```
frontend/src/
├── stores/
│   └── auth-store.ts
├── lib/api/
│   └── auth.ts
└── hooks/
    └── use-auth.ts
```

#### 验收标准

- [ ] AC-1: Zustand auth store实现
- [ ] AC-2: Token存储（httpOnly cookie或localStorage）
- [ ] AC-3: 自动刷新Token
- [ ] AC-4: 401自动跳转登录

#### 代码模板

**stores/auth-store.ts**
```typescript
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  email: string
  name: string
  role: string
  credits_balance: number
}

interface AuthState {
  user: User | null
  accessToken: string | null
  isAuthenticated: boolean
  setAuth: (user: User, token: string) => void
  logout: () => void
  updateCredits: (balance: number) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      setAuth: (user, token) => set({ 
        user, 
        accessToken: token, 
        isAuthenticated: true 
      }),
      logout: () => set({ 
        user: null, 
        accessToken: null, 
        isAuthenticated: false 
      }),
      updateCredits: (balance) => set((state) => ({
        user: state.user ? { ...state.user, credits_balance: balance } : null
      }))
    }),
    { name: 'auth-storage' }
  )
)
```

---

### M1-10: 登录注册页面

```yaml
---
id: M1-10
title: 登录注册页面
executor: mini-agent
priority: P0
estimated_hours: 4
task_type: coding
dependencies:
  - M0-07
  - M1-09
outputs:
  - frontend/src/app/(auth)/login/page.tsx
  - frontend/src/app/(auth)/register/page.tsx
  - frontend/src/i18n/messages/zh.json
  - frontend/src/i18n/messages/en.json
acceptance_criteria:
  - /login 页面可用
  - /register 页面可用
  - 表单验证（Zod + React Hook Form）
  - 错误提示友好
  - 响应式设计
  - i18n支持（中英文）
---
```

#### 描述

实现登录和注册页面UI。

#### 输入

- shadcn/ui组件库 (M0-07)
- 前端认证状态管理 (M1-09)

#### 输出文件

```
frontend/src/
├── app/(auth)/
│   ├── login/
│   │   └── page.tsx
│   └── register/
│       └── page.tsx
└── i18n/messages/
    ├── zh.json
    └── en.json
```

#### 验收标准

- [ ] AC-1: /login 页面可用
- [ ] AC-2: /register 页面可用
- [ ] AC-3: 表单验证（Zod + React Hook Form）
- [ ] AC-4: 错误提示友好
- [ ] AC-5: 响应式设计
- [ ] AC-6: i18n支持（中英文）

#### 代码模板

**app/(auth)/login/page.tsx**
```typescript
'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { useTranslations } from 'next-intl'

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
})

export default function LoginPage() {
  const t = useTranslations('auth')
  const form = useForm({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: z.infer<typeof loginSchema>) => {
    // 登录逻辑
  }

  return (
    <Card className="w-[400px]">
      <CardHeader>
        <h1 className="text-2xl font-bold">{t('login.title')}</h1>
      </CardHeader>
      <CardContent>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          {/* 表单字段 */}
        </form>
      </CardContent>
    </Card>
  )
}
```

---

## 里程碑检查点

### 完成标准

- [ ] 用户可注册新账号
- [ ] 用户可登录/登出
- [ ] JWT认证正常工作
- [ ] 前端认证流程完整
- [ ] 密码可重置

### 交付物

1. 认证API完整实现
2. 前端登录注册页面
3. 认证状态管理
4. 单元测试

---

## 安全注意事项

| 项目 | 措施 |
|------|------|
| 密码存储 | bcrypt加密，不存储明文 |
| Token安全 | 短期access_token + 长期refresh_token |
| 暴力破解防护 | 登录失败计数，IP限流 |
| XSS防护 | httpOnly cookie存储Token |
| CSRF防护 | SameSite cookie属性 |

---

> 📝 **文档版本**: 2.0 | **更新日期**: 2026-01-25 | **变更**: 添加 YAML Front Matter，统一验收标准格式
