# BidAgent V2 — 编码规范

> 版本: 1.0.0 | 日期: 2026-02-11 | 状态: Enforced
>
> 本文档是项目开发过程中**必须遵守**的编码规范。所有代码提交前须对照检查。
> 与 `07-dev-standards.md` (架构层设计规范) 互补，本文聚焦**编码实践细节**。

---

## 目录

1. [Python 编码规范](#1-python-编码规范)
2. [TypeScript / React 编码规范](#2-typescript--react-编码规范)
3. [SQL 与数据库规范](#3-sql-与数据库规范)
4. [API 设计规范](#4-api-设计规范)
5. [错误处理规范](#5-错误处理规范)
6. [安全编码规范](#6-安全编码规范)
7. [日志规范](#7-日志规范)
8. [测试编码规范](#8-测试编码规范)
9. [性能编码规范](#9-性能编码规范)
10. [Git 提交与 Code Review 规范](#10-git-提交与-code-review-规范)
11. [禁止清单](#11-禁止清单)

---

## 1. Python 编码规范

### 1.1 格式化与工具链

| 工具 | 用途 | 配置 |
|------|------|------|
| Ruff | Lint + Format | `line-length=88`, `target-version="py312"` |
| mypy | 类型检查 | `strict=true` (渐进开启) |
| pytest | 测试 | `asyncio_mode=auto` |

```bash
# 提交前必须通过
ruff check .
ruff format --check .
pytest -v
```

### 1.2 导入规范

**顺序**: 标准库 → 第三方库 → 本地模块，每组之间空一行。

```python
# ✅ 正确
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.services.user_service import UserService
```

```python
# ❌ 错误 — 混合分组、无序
from app.models.user import User
from datetime import datetime
import uuid
from fastapi import Depends
from app.services.user_service import UserService
from sqlalchemy import select
```

**规则**:
- 禁止 `from module import *`
- 禁止相对导入 (`from ..models import`)，统一使用 `from app.xxx`
- 同一模块的多个导入合并为一行 (除非超长)

### 1.3 命名规范

| 类别 | 风格 | 示例 |
|------|------|------|
| 模块/文件 | `snake_case` | `user_service.py`, `bid_analysis.py` |
| 函数/方法 | `snake_case` | `get_by_email()`, `run_analysis_pipeline()` |
| 类 | `PascalCase` | `UserService`, `AnalyzeQualification` |
| 常量 | `UPPER_SNAKE_CASE` | `MAX_UPLOAD_SIZE`, `DEFAULT_PAGE_SIZE` |
| 私有属性 | `_leading_underscore` | `_validate_input()`, `_cache` |
| 受保护 | `_single_underscore` | `_build_query()` |
| 布尔变量 | `is_/has_/can_/should_` 前缀 | `is_active`, `has_permission`, `can_edit` |
| 枚举值 | `UPPER_SNAKE_CASE` | `ProjectStatus.ANALYZING` |

```python
# ✅ 正确
class BidDocumentService:
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._cache: dict[str, Any] = {}
    
    async def get_by_project_id(self, project_id: uuid.UUID) -> list[BidDocument]:
        ...
    
    async def is_processing_complete(self, doc_id: uuid.UUID) -> bool:
        ...
    
    def _validate_file_type(self, filename: str) -> bool:
        ...
```

### 1.4 类型提示

**所有公开函数必须有完整类型提示**。私有函数推荐但不强制。

```python
# ✅ 正确 — 完整类型提示
async def create_project(
    self,
    user_id: uuid.UUID,
    data: ProjectCreate,
) -> Project:
    ...

async def search_opportunities(
    self,
    query: str,
    source: OpportunitySource | None = None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResult[Opportunity]:
    ...

def calculate_similarity(
    self,
    embedding_a: list[float],
    embedding_b: list[float],
) -> float:
    ...
```

```python
# ❌ 错误 — 缺少类型提示
async def create_project(self, user_id, data):
    ...

# ❌ 错误 — 使用 Any 逃避
async def process_document(self, doc: Any) -> Any:
    ...
```

**类型提示最佳实践**:

```python
from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from typing import Any, TypeVar

# 使用 | 替代 Union
def get_user(user_id: str | None = None) -> User | None: ...

# 使用 collections.abc 替代 typing
def get_items() -> Sequence[Item]: ...
async def stream_response() -> AsyncGenerator[str, None]: ...

# 泛型
T = TypeVar("T")
async def paginate(query: Select, page: int) -> PaginatedResult[T]: ...

# TypedDict 用于复杂 dict
class AnalysisResult(TypedDict):
    qualification: dict[str, Any]
    criteria: dict[str, Any]
    risk_score: float
```

### 1.5 函数与方法

**单一职责**: 每个函数做一件事，函数体不超过 50 行 (不含 docstring)。

```python
# ✅ 正确 — 清晰的单一职责
async def upload_document(
    self,
    project_id: uuid.UUID,
    file: UploadFile,
) -> BidDocument:
    """上传并创建文档记录，触发异步处理。"""
    self._validate_file(file)
    file_path = await self._save_file(file)
    file_hash = self._compute_hash(file_path)
    
    document = await self._create_record(project_id, file, file_path, file_hash)
    await self._dispatch_processing_task(document.id)
    
    return document
```

```python
# ❌ 错误 — 函数过长/职责混乱
async def upload_and_process_and_analyze_document(self, project_id, file):
    # 200 行代码，既做上传又做解析又做分析...
    ...
```

**参数规则**:
- 参数 ≤ 5 个；超过 5 个用 dataclass 或 Pydantic model 封装
- 布尔参数必须用关键字传参: `def search(*, fuzzy: bool = False)`
- 避免可变默认值: 用 `None` + 函数内赋值

```python
# ✅ 正确 — 超过 5 个参数时用 model 封装
class SearchParams(BaseModel):
    query: str
    source: OpportunitySource | None = None
    country: str | None = None
    sector: str | None = None
    status: OpportunityStatus | None = None
    page: int = 1
    page_size: int = 20

async def search(self, params: SearchParams) -> PaginatedResult[Opportunity]:
    ...

# ✅ 正确 — 布尔参数强制关键字
async def run_analysis(self, project_id: uuid.UUID, *, force_refresh: bool = False) -> AnalysisResult:
    ...
```

### 1.6 Docstring 规范

公开类和公开方法必须有 Google style docstring。

```python
class BidAnalysisService:
    """招标分析服务。
    
    负责执行 8 步分析管道，管理分析结果缓存，
    支持增量分析和强制刷新。
    """
    
    async def run_pipeline(
        self,
        project_id: uuid.UUID,
        *,
        force_refresh: bool = False,
    ) -> AnalysisResult:
        """执行完整的 8 步分析管道。
        
        Args:
            project_id: 目标项目 ID。
            force_refresh: 是否忽略缓存强制重新分析。
            
        Returns:
            包含 8 个维度分析结果的 AnalysisResult。
            
        Raises:
            NotFoundError: 项目不存在。
            InsufficientCreditsError: 积分不足。
            LLMError: LLM 调用失败且重试耗尽。
        """
        ...
```

### 1.7 异步编程

```python
# ✅ 正确 — 并行执行无依赖的异步操作
async def get_project_overview(self, project_id: uuid.UUID) -> ProjectOverview:
    project, documents, analysis = await asyncio.gather(
        self.project_service.get_by_id(project_id),
        self.document_service.list_by_project(project_id),
        self.analysis_service.get_latest(project_id),
    )
    return ProjectOverview(project=project, documents=documents, analysis=analysis)
```

```python
# ❌ 错误 — 串行等待无依赖操作
async def get_project_overview(self, project_id: uuid.UUID):
    project = await self.project_service.get_by_id(project_id)
    documents = await self.document_service.list_by_project(project_id)
    analysis = await self.analysis_service.get_latest(project_id)
```

```python
# ❌ 错误 — 在异步上下文中使用阻塞 I/O
async def process_pdf(self, file_path: str):
    with open(file_path, "rb") as f:  # ❌ 阻塞 I/O
        content = f.read()
    
# ✅ 正确 — 使用 aiofiles 或 run_in_executor
async def process_pdf(self, file_path: str):
    content = await asyncio.to_thread(Path(file_path).read_bytes)
```

### 1.8 Service 层模式

```python
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """项目管理服务。"""
    
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
    
    async def get_by_id(self, project_id: uuid.UUID) -> Project:
        """获取项目，不存在时抛出 NotFoundError。"""
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if project is None:
            raise NotFoundError(resource_type="Project", resource_id=str(project_id))
        return project
    
    async def create(self, user_id: uuid.UUID, data: ProjectCreate) -> Project:
        """创建项目。"""
        project = Project(
            user_id=user_id,
            title=data.title,
            institution=data.institution,
            opportunity_id=data.opportunity_id,
        )
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project
    
    async def update(self, project_id: uuid.UUID, data: ProjectUpdate) -> Project:
        """部分更新项目。"""
        project = await self.get_by_id(project_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)
        await self.db.commit()
        await self.db.refresh(project)
        return project
    
    async def list_by_user(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResult[Project]:
        """分页获取用户项目列表。"""
        base_query = select(Project).where(Project.user_id == user_id)
        
        # 计算总数
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        
        # 分页查询
        items_query = (
            base_query
            .order_by(Project.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(items_query)
        items = list(result.scalars().all())
        
        return PaginatedResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )
```

### 1.9 Pydantic Schema 模式

```python
from pydantic import BaseModel, Field, field_validator, EmailStr
import uuid
from datetime import datetime


class ProjectCreate(BaseModel):
    """创建项目请求。"""
    title: str = Field(..., min_length=1, max_length=200, description="项目标题")
    institution: str = Field(..., pattern=r"^(adb|wb|un)$", description="机构标识")
    opportunity_id: uuid.UUID | None = Field(None, description="关联招标信息 ID")
    description: str | None = Field(None, max_length=2000)
    
    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("标题不能为空白")
        return v.strip()


class ProjectResponse(BaseModel):
    """项目响应。"""
    id: uuid.UUID
    title: str
    institution: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class ProjectUpdate(BaseModel):
    """部分更新项目。所有字段可选。"""
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
```

---

## 2. TypeScript / React 编码规范

### 2.1 格式化与工具链

| 工具 | 用途 | 配置 |
|------|------|------|
| Prettier | Format | `semi: false`, `singleQuote: false`, `tabWidth: 2` |
| ESLint | Lint | `@next/eslint-plugin-next` + `@typescript-eslint` |
| TypeScript | 类型检查 | `strict: true` |

```bash
# 提交前必须通过
npm run lint
npm run build  # 包含 tsc 类型检查
```

### 2.2 文件命名

| 类别 | 命名 | 示例 |
|------|------|------|
| 页面 | `page.tsx` (Next.js 约定) | `app/[locale]/projects/page.tsx` |
| 布局 | `layout.tsx` | `app/[locale]/layout.tsx` |
| 组件文件 | `PascalCase.tsx` | `OppSearchPanel.tsx`, `BidChatPanel.tsx` |
| Hook 文件 | `kebab-case.ts` | `use-auth.ts`, `use-projects.ts` |
| Service 文件 | `kebab-case.ts` | `api-client.ts`, `bid-analysis.ts` |
| Type 文件 | `kebab-case.ts` | `auth.ts`, `opportunity.ts` |
| Store 文件 | `kebab-case.ts` | `auth.ts`, `bid-workspace.ts` |
| 工具文件 | `kebab-case.ts` | `format-date.ts`, `cn.ts` |

### 2.3 组件规范

```tsx
// ✅ 正确 — 标准组件写法
import { memo } from "react"
import { useTranslations } from "next-intl"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { Project } from "@/types/project"

interface ProjectCardProps {
  project: Project
  onSelect: (projectId: string) => void
  isActive?: boolean
}

function ProjectCard({ project, onSelect, isActive = false }: ProjectCardProps) {
  const t = useTranslations("projects")

  return (
    <Card
      className={cn("cursor-pointer transition-shadow hover:shadow-md", {
        "ring-2 ring-primary": isActive,
      })}
      onClick={() => onSelect(project.id)}
    >
      <CardHeader>
        <CardTitle className="text-lg">{project.title}</CardTitle>
        <Badge variant={getStatusVariant(project.status)}>
          {t(`status.${project.status}`)}
        </Badge>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{project.description}</p>
      </CardContent>
    </Card>
  )
}

export default memo(ProjectCard)
```

**组件规则**:
- 使用 `function` 声明 (非箭头函数) 定义组件
- `memo()` 包裹所有接收复杂 props 的组件
- 每个组件必须定义 `interface XxxProps`
- Props interface 放在组件之前，同一文件
- 禁止在组件文件内定义多个导出组件
- `export default` 用于页面/布局组件，`export` 用于共享组件

### 2.4 类型定义

```typescript
// types/project.ts

// ✅ 正确 — 使用 interface 定义对象类型
export interface Project {
  id: string
  title: string
  institution: Institution
  status: ProjectStatus
  description: string | null
  createdAt: string
  updatedAt: string
}

// ✅ 正确 — 使用 type 定义联合/交叉类型
export type Institution = "adb" | "wb" | "un"

export type ProjectStatus =
  | "draft"
  | "analyzing"
  | "guiding"
  | "review"
  | "submitted"
  | "won"
  | "lost"

// ✅ 正确 — 请求/响应类型
export interface CreateProjectRequest {
  title: string
  institution: Institution
  opportunityId?: string
  description?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  pages: number
}
```

```typescript
// ❌ 错误 — 使用 any
const data: any = response.data

// ✅ 正确 — 使用 unknown + 类型守卫
const data: unknown = response.data
if (isProject(data)) {
  // data is Project
}

// ❌ 错误 — 使用 as 强制断言 (除非必要)
const project = response.data as Project

// ✅ 正确 — 使用泛型
const project = await apiClient.get<Project>(`/projects/${id}`)
```

### 2.5 Hooks 规范

```typescript
// hooks/use-projects.ts

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { projectsService } from "@/services/projects"
import type { CreateProjectRequest, Project } from "@/types/project"

const QUERY_KEYS = {
  projects: ["projects"] as const,
  project: (id: string) => ["projects", id] as const,
}

export function useProjects(page: number = 1) {
  return useQuery({
    queryKey: [...QUERY_KEYS.projects, page],
    queryFn: () => projectsService.list(page),
  })
}

export function useProject(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.project(id),
    queryFn: () => projectsService.getById(id),
    enabled: !!id,
  })
}

export function useCreateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateProjectRequest) => projectsService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.projects })
    },
  })
}
```

**Hook 规则**:
- 每个 API 资源对应一个 hook 文件
- Query keys 集中定义为常量对象
- `enabled` 用于条件查询
- `onSuccess` 中 invalidate 相关缓存
- 避免在 hook 中嵌入业务逻辑

### 2.6 Service 层规范

```typescript
// services/api-client.ts

import axios from "axios"

import { useAuthStore } from "@/stores/auth"

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL,
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
})

// 请求拦截: 注入 JWT
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截: 积分追踪 + 401 自动刷新
apiClient.interceptors.response.use(
  (response) => {
    const consumed = response.headers["x-credits-consumed"]
    const remaining = response.headers["x-credits-remaining"]
    if (consumed) {
      useAuthStore.getState().updateCredits(Number(remaining))
    }
    return response
  },
  async (error) => {
    if (error.response?.status === 401) {
      // Token 刷新逻辑
      const refreshed = await attemptTokenRefresh()
      if (refreshed) {
        return apiClient.request(error.config)
      }
      useAuthStore.getState().logout()
    }
    return Promise.reject(error)
  },
)

export { apiClient }
```

```typescript
// services/projects.ts

import { apiClient } from "./api-client"
import type {
  CreateProjectRequest,
  PaginatedResponse,
  Project,
} from "@/types/project"

export const projectsService = {
  list: async (page: number = 1): Promise<PaginatedResponse<Project>> => {
    const { data } = await apiClient.get("/projects", { params: { page } })
    return data
  },

  getById: async (id: string): Promise<Project> => {
    const { data } = await apiClient.get(`/projects/${id}`)
    return data
  },

  create: async (request: CreateProjectRequest): Promise<Project> => {
    const { data } = await apiClient.post("/projects", request)
    return data
  },

  update: async (id: string, request: Partial<CreateProjectRequest>): Promise<Project> => {
    const { data } = await apiClient.patch(`/projects/${id}`, request)
    return data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/projects/${id}`)
  },
}
```

### 2.7 Zustand Store 规范

```typescript
// stores/auth.ts

import { create } from "zustand"
import { persist } from "zustand/middleware"

interface AuthState {
  // State
  accessToken: string | null
  user: User | null
  creditsBalance: number

  // Actions
  setAuth: (token: string, user: User) => void
  updateCredits: (balance: number) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      user: null,
      creditsBalance: 0,

      setAuth: (accessToken, user) =>
        set({ accessToken, user, creditsBalance: user.creditsBalance }),

      updateCredits: (creditsBalance) => set({ creditsBalance }),

      logout: () => set({ accessToken: null, user: null, creditsBalance: 0 }),
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({
        accessToken: state.accessToken,
        user: state.user,
      }),
    },
  ),
)
```

**Store 规则**:
- State 和 Actions 分区定义在同一 interface
- 使用 `persist` 中间件仅持久化必要字段
- 服务器数据用 TanStack Query，客户端状态用 Zustand — **不混用**
- Store 文件与状态域一一对应: `auth.ts`, `ui.ts`, `bid-workspace.ts`

### 2.8 国际化 (i18n)

```tsx
// ✅ 正确 — 所有 UI 文本走 next-intl
function LoginForm() {
  const t = useTranslations("auth")
  
  return (
    <form>
      <label>{t("email")}</label>
      <Input placeholder={t("emailPlaceholder")} />
      <Button>{t("login")}</Button>
      <p>{t("noAccount")} <Link href="/register">{t("register")}</Link></p>
    </form>
  )
}
```

```tsx
// ❌ 错误 — 硬编码中文/英文
function LoginForm() {
  return (
    <form>
      <label>邮箱</label>
      <Button>登录</Button>
    </form>
  )
}
```

**翻译文件结构**:
```json
// i18n/messages/zh.json
{
  "auth": {
    "email": "邮箱",
    "emailPlaceholder": "请输入邮箱地址",
    "login": "登录",
    "register": "注册",
    "noAccount": "还没有账号？"
  },
  "projects": {
    "title": "我的项目",
    "create": "新建项目",
    "status": {
      "draft": "草稿",
      "analyzing": "分析中",
      "guiding": "指导中"
    }
  }
}
```

**规则**:
- Key 使用嵌套结构: `{namespace}.{section}.{key}`
- 动态值用 ICU MessageFormat: `t("welcome", { name: user.name })`
- 日期用 `date-fns` + locale，不在翻译文件中写日期格式

### 2.9 CSS / Tailwind 规范

```tsx
// ✅ 正确 — 使用 cn() 合并动态 class
import { cn } from "@/lib/utils"

function StatusBadge({ status, className }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-1 text-xs font-medium",
        {
          "bg-green-100 text-green-800": status === "active",
          "bg-yellow-100 text-yellow-800": status === "pending",
          "bg-red-100 text-red-800": status === "failed",
        },
        className,
      )}
    >
      {status}
    </span>
  )
}
```

**规则**:
- 优先使用 Tailwind utility classes
- 动态样式用 `cn()` (clsx + tailwind-merge)
- 避免内联 `style={{}}`，除非动态计算值 (如百分比)
- 响应式: `sm:` → `md:` → `lg:` → `xl:` (移动优先)
- 暗色模式预留: 使用 `bg-background`, `text-foreground` 等 CSS 变量

---

## 3. SQL 与数据库规范

### 3.1 表命名

| 类别 | 命名 | 示例 |
|------|------|------|
| 表名 | 复数 `snake_case` | `users`, `bid_documents`, `knowledge_chunks` |
| 列名 | 单数 `snake_case` | `user_id`, `created_at`, `file_hash` |
| 索引 | `idx_{table}_{columns}` | `idx_opportunities_source_status` |
| 约束 | `{table}_{type}_{columns}` | `users_uq_email`, `projects_fk_user_id` |
| ENUM | `{domain}_{name}` | `user_role`, `project_status`, `opportunity_source` |

### 3.2 必需列

每张表**必须**包含:

```sql
id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
```

软删除表额外包含:

```sql
deleted_at   TIMESTAMPTZ DEFAULT NULL
```

### 3.3 外键规范

```sql
-- ✅ 正确 — 显式命名 + ON DELETE 策略
ALTER TABLE projects
  ADD CONSTRAINT projects_fk_user_id
  FOREIGN KEY (user_id) REFERENCES users(id)
  ON DELETE CASCADE;

-- ✅ 正确 — 可空外键用 SET NULL
ALTER TABLE projects
  ADD CONSTRAINT projects_fk_opportunity_id
  FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
  ON DELETE SET NULL;
```

**ON DELETE 策略选择**:

| 关系 | 策略 | 示例 |
|------|------|------|
| 强依赖 (所有者删除则级联) | `CASCADE` | `projects → users` |
| 弱关联 (保留记录) | `SET NULL` | `projects → opportunities` |
| 禁止删除 (有子记录时阻止) | `RESTRICT` | `knowledge_bases → knowledge_chunks` |

### 3.4 向量列规范

```sql
-- 统一 1024 维
embedding    vector(1024)

-- HNSW 索引 (统一参数)
CREATE INDEX idx_{table}_embedding ON {table}
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- 查询模板
SELECT content, 1 - (embedding <=> $1::vector) AS similarity
FROM {table}
WHERE similarity > 0.6  -- score_threshold
ORDER BY embedding <=> $1::vector
LIMIT 10;
```

### 3.5 SQLAlchemy ORM 规范

```python
# ✅ 正确 — 查询用 select()，不用 session.query()
from sqlalchemy import select, func

# 单条查询
result = await db.execute(select(User).where(User.email == email))
user = result.scalar_one_or_none()

# 列表查询
result = await db.execute(
    select(Project)
    .where(Project.user_id == user_id)
    .order_by(Project.updated_at.desc())
    .limit(20)
)
projects = list(result.scalars().all())

# 聚合查询
result = await db.execute(
    select(func.count()).select_from(Project).where(Project.user_id == user_id)
)
total = result.scalar() or 0

# 关联查询 (eager loading)
result = await db.execute(
    select(Project)
    .options(selectinload(Project.documents))
    .where(Project.id == project_id)
)
```

```python
# ❌ 错误 — 使用 1.x 风格 session.query()
users = db.query(User).filter(User.email == email).first()
```

### 3.6 迁移规范

```python
# alembic/versions/001_users_and_auth.py

"""创建用户和认证相关表。

Revision ID: 001
Create Date: 2026-02-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ENUM

# revision identifiers
revision = "001"
down_revision = None

user_role = ENUM("user", "admin", name="user_role", create_type=False)

def upgrade() -> None:
    # 创建 ENUM
    user_role.create(op.get_bind(), checkfirst=True)
    
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

def downgrade() -> None:
    op.drop_table("users")
    user_role.drop(op.get_bind(), checkfirst=True)
```

**迁移规则**:
- 每个迁移有清晰的 `upgrade()` 和 `downgrade()`
- 顶部 docstring 说明变更内容
- ENUM 创建在 `upgrade()` 中，删除在 `downgrade()` 中
- 数据迁移与结构迁移分离

---

## 4. API 设计规范

### 4.1 RESTful 路由

```
GET    /api/v1/{resource}                 # 列表 (分页)
POST   /api/v1/{resource}                 # 创建
GET    /api/v1/{resource}/{id}            # 详情
PATCH  /api/v1/{resource}/{id}            # 部分更新
DELETE /api/v1/{resource}/{id}            # 删除
POST   /api/v1/{resource}/{id}/{action}   # 操作 (非 CRUD)
```

### 4.2 路由文件模式

```python
# api/v1/projects.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的项目列表。"""
    service = ProjectService(db)
    return await service.list_by_user(current_user.id, page=page, page_size=page_size)


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建新项目。"""
    service = ProjectService(db)
    return await service.create(current_user.id, data)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取项目详情。"""
    service = ProjectService(db)
    project = await service.get_by_id(project_id)
    # 权限检查: 只能访问自己的项目
    if project.user_id != current_user.id:
        raise AuthorizationError()
    return project
```

**路由编写规则**:
- 路由函数**不包含业务逻辑**，仅负责: 参数解析 → 调用 Service → 返回结果
- 每个路由函数有 docstring
- Service 实例在路由函数内创建 (不是全局单例)
- 权限检查在路由层完成
- `response_model` 显式声明返回类型

### 4.3 分页响应

```python
# schemas/common.py

from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    """统一分页响应。"""
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int
    
    @classmethod
    def create(cls, items: list[T], total: int, page: int, page_size: int):
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size,
        )
```

### 4.4 HTTP 状态码

| 场景 | 状态码 |
|------|--------|
| 查询成功 | `200 OK` |
| 创建成功 | `201 Created` |
| 删除成功（无返回体） | `204 No Content` |
| 请求参数错误 | `400 Bad Request` |
| 未认证 | `401 Unauthorized` |
| 积分不足 | `402 Payment Required` |
| 无权限 | `403 Forbidden` |
| 资源不存在 | `404 Not Found` |
| 字段校验失败 | `422 Unprocessable Entity` |
| 频率限制 | `429 Too Many Requests` |
| 服务器错误 | `500 Internal Server Error` |
| 外部服务失败 (LLM/爬虫) | `502 Bad Gateway` |

---

## 5. 错误处理规范

### 5.1 后端异常层次

```python
# core/exceptions.py

class BidAgentException(Exception):
    """所有业务异常基类。"""
    code: str = "INTERNAL_ERROR"
    status_code: int = 500
    message: str = "Internal server error"

    def __init__(self, message: str | None = None, **kwargs: Any) -> None:
        if message:
            self.message = message
        self.details = kwargs
        super().__init__(self.message)


class NotFoundError(BidAgentException):
    code = "NOT_FOUND"
    status_code = 404

    def __init__(self, resource_type: str, resource_id: str) -> None:
        super().__init__(message=f"{resource_type} {resource_id} not found")


class InsufficientCreditsError(BidAgentException):
    code = "INSUFFICIENT_CREDITS"
    status_code = 402

    def __init__(self, required: int, available: int) -> None:
        super().__init__(
            message=f"Insufficient credits: need {required}, have {available}",
            required=required,
            available=available,
        )
```

**规则**:
- 所有业务异常继承 `BidAgentException`
- 禁止在 Service 层抛出 `HTTPException` (那是 FastAPI 层的职责)
- 禁止 bare `except:` 或 `except Exception:` 然后吞掉异常
- 异常信息不泄露敏感信息 (数据库连接串、文件路径等)

### 5.2 前端错误处理

```typescript
// ✅ 正确 — 统一错误处理
import { toast } from "@/components/ui/use-toast"

function handleApiError(error: unknown): void {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status
    const message = error.response?.data?.message ?? "请求失败"

    switch (status) {
      case 401:
        // 由 interceptor 处理
        break
      case 402:
        toast({ title: "积分不足", description: message, variant: "destructive" })
        break
      case 404:
        toast({ title: "资源不存在", description: message })
        break
      default:
        toast({ title: "操作失败", description: message, variant: "destructive" })
    }
  } else {
    toast({ title: "网络错误", description: "请检查网络连接", variant: "destructive" })
  }
}
```

```typescript
// ✅ 正确 — Mutation 错误处理
export function useCreateProject() {
  return useMutation({
    mutationFn: projectsService.create,
    onError: handleApiError,
  })
}
```

---

## 6. 安全编码规范

### 6.1 认证

```python
# ✅ 正确 — 密码哈希
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

### 6.2 输入验证

```python
# ✅ 正确 — Pydantic 自动验证
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=1, max_length=100)
    
    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("密码必须包含大写字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含数字")
        return v
```

### 6.3 SQL 注入防护

```python
# ✅ 正确 — 使用参数化查询
result = await db.execute(
    select(User).where(User.email == email)
)

# ✅ 正确 — 使用 text() 绑定参数
from sqlalchemy import text
result = await db.execute(
    text("SELECT * FROM users WHERE email = :email"),
    {"email": email},
)

# ❌ 禁止 — 字符串拼接 SQL
result = await db.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

### 6.4 文件上传安全

```python
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def validate_upload(file: UploadFile) -> None:
    """验证上传文件的安全性。"""
    # 1. 检查文件大小
    if file.size and file.size > MAX_FILE_SIZE:
        raise ValidationError("文件大小不能超过 50MB")
    
    # 2. 检查扩展名
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"不支持的文件类型: {ext}")
    
    # 3. 检查 MIME 类型
    allowed_mimes = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    if file.content_type not in allowed_mimes:
        raise ValidationError(f"不支持的文件类型: {file.content_type}")
    
    # 4. 使用 UUID 重命名 (防止路径遍历)
    safe_filename = f"{uuid.uuid4()}{ext}"
    return safe_filename
```

### 6.5 敏感数据

```python
# ❌ 禁止 — 日志输出密码/token/API key
logger.info("User login: email=%s, password=%s", email, password)
logger.info("LLM API key: %s", api_key)

# ✅ 正确 — 脱敏
logger.info("User login: email=%s", email)
logger.info("LLM request: model=%s, tokens=%d", model, token_count)

# ❌ 禁止 — 返回密码哈希
class UserResponse(BaseModel):
    password_hash: str  # 绝对不行

# ✅ 正确 — Schema 中排除敏感字段
class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    # 不包含 password_hash
```

---

## 7. 日志规范

### 7.1 日志级别

| 级别 | 用途 | 示例 |
|------|------|------|
| `DEBUG` | 开发调试 | 调用参数、中间变量 |
| `INFO` | 正常业务流 | 用户登录、分析开始、爬虫完成 |
| `WARNING` | 可恢复异常 | LLM 重试、Embedding 降级 |
| `ERROR` | 需关注的错误 | LLM 最终失败、数据库异常 |
| `CRITICAL` | 系统不可用 | 数据库连接断开、Redis 不可达 |

### 7.2 日志格式

```python
import logging
import structlog  # 推荐

logger = structlog.get_logger(__name__)

# ✅ 正确 — 结构化 + 带上下文
await logger.ainfo(
    "analysis_pipeline_started",
    project_id=str(project_id),
    user_id=str(user_id),
    force_refresh=force_refresh,
)

await logger.ainfo(
    "analysis_pipeline_completed",
    project_id=str(project_id),
    duration_ms=elapsed_ms,
    steps_completed=8,
    credits_consumed=15,
)

# ✅ 正确 — 错误带异常信息
await logger.aerror(
    "llm_call_failed",
    project_id=str(project_id),
    model=model_name,
    retry_count=3,
    exc_info=True,
)
```

```python
# ❌ 错误 — 不要用 f-string 拼日志 (影响性能/结构化)
logger.info(f"Project {project_id} analysis started by {user_id}")

# ❌ 错误 — 不要 print
print("debug:", result)
```

### 7.3 生产环境 JSON 输出

```json
{
  "timestamp": "2026-02-11T10:30:00.123Z",
  "level": "info",
  "event": "analysis_pipeline_completed",
  "logger": "app.services.bid_analysis",
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "duration_ms": 3500,
  "credits_consumed": 15
}
```

---

## 8. 测试编码规范

### 8.1 测试命名

```python
# 格式: test_{被测方法}_{场景}_{预期结果}

# ✅ 正确
async def test_create_project_with_valid_data_returns_201():
async def test_create_project_without_token_returns_401():
async def test_create_project_with_invalid_institution_returns_422():
async def test_get_project_by_other_user_returns_403():
async def test_search_opportunities_with_empty_query_returns_all():

# ❌ 错误 — 含义不清
async def test_project():
async def test_create():
async def test_it_works():
```

### 8.2 测试结构 (AAA 模式)

```python
@pytest.mark.asyncio
async def test_create_project_with_valid_data_returns_201(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    # Arrange — 准备数据
    request_data = {
        "title": "ADB Test Project",
        "institution": "adb",
        "description": "Testing project creation",
    }

    # Act — 执行操作
    response = await client.post(
        "/api/v1/projects",
        json=request_data,
        headers=auth_headers,
    )

    # Assert — 验证结果
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "ADB Test Project"
    assert data["institution"] == "adb"
    assert data["status"] == "draft"
    assert "id" in data
    assert "created_at" in data
```

### 8.3 Fixture 规范

```python
# conftest.py

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/bidagent_test"


@pytest.fixture(scope="session")
def event_loop():
    """Session-scoped event loop."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """每个测试函数独立的数据库 session (自动回滚)。"""
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """注入测试 session 的 AsyncClient。"""
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """创建测试用户。"""
    user = User(
        email="test@example.com",
        password_hash=hash_password("Test1234!"),
        name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """带 JWT 的认证 headers。"""
    token = create_access_token(user_id=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_llm() -> Generator[AsyncMock, None, None]:
    """Mock LLM Client (不调用真实 API)。"""
    with patch("app.agents.llm_client.LLMClient") as mock_cls:
        instance = AsyncMock()
        instance.chat.return_value = {"content": "mock response"}
        mock_cls.return_value = instance
        yield instance
```

### 8.4 Mock 规范

```python
# ✅ 正确 — Mock 外部依赖 (LLM / Embedding / 爬虫)
@pytest.mark.asyncio
async def test_analyze_qualification_with_mock_llm(mock_llm):
    mock_llm.chat.return_value = {
        "content": json.dumps({
            "legal": [{"requirement": "Registered company", "met": True}],
            "financial": [],
            "technical": [],
            "experience": [],
        })
    }
    
    skill = AnalyzeQualification(llm_client=mock_llm)
    result = await skill.execute(context=...)
    
    assert result.success is True
    assert len(result.data["legal"]) == 1

# ✅ 正确 — 不 Mock 数据库 (使用真实测试库)
@pytest.mark.asyncio
async def test_create_user_saves_to_database(db_session):
    service = UserService(db_session)
    user = await service.register(RegisterRequest(
        email="new@example.com",
        password="Test1234!",
        name="New User",
    ))
    
    # 直接查库验证
    result = await db_session.execute(select(User).where(User.id == user.id))
    saved_user = result.scalar_one()
    assert saved_user.email == "new@example.com"
```

**Mock 规则**:
- **Mock 外部依赖**: LLM API / Embedding API / 第三方爬虫 / 邮件 / 支付
- **不 Mock 数据库**: 使用独立测试库 + 每测试回滚
- **不 Mock 业务逻辑**: Service 层用真实实现测试

### 8.5 测试覆盖率

| 层 | 最低覆盖率 | 重点 |
|----|-----------|------|
| `services/` | **≥90%** | 全部公开方法 + 边界情况 |
| `api/v1/` | **≥80%** | 正常流 + 认证 + 错误码 |
| `agents/skills/` | **≥80%** | execute() + 输入验证 + JSON 解析容错 |
| `core/` | **≥90%** | 安全 + 异常 + 中间件 |
| `crawlers/` | **≥70%** | HTML 解析 + 错误处理 (Mock HTTP) |

---

## 9. 性能编码规范

### 9.1 数据库查询

```python
# ✅ 正确 — 避免 N+1: 使用 selectinload
result = await db.execute(
    select(Project)
    .options(selectinload(Project.documents))
    .where(Project.user_id == user_id)
)

# ❌ 错误 — N+1: 循环中查询关联
projects = await get_projects(user_id)
for p in projects:
    p.documents = await get_documents(p.id)  # ❌ N 次查询
```

```python
# ✅ 正确 — 只查需要的列
result = await db.execute(
    select(Opportunity.id, Opportunity.title, Opportunity.deadline)
    .where(Opportunity.source == "adb")
)

# ❌ 错误 — SELECT * 查全部列 (特别是含 TSVECTOR/TEXT 大列)
result = await db.execute(select(Opportunity))
```

### 9.2 缓存策略

```python
# ✅ 正确 — Redis 缓存热点数据
import json

async def get_analysis_result(self, project_id: uuid.UUID) -> dict:
    cache_key = f"analysis:{project_id}"
    
    # 查缓存
    cached = await self.redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # 查库
    result = await self._query_analysis(project_id)
    
    # 写缓存 (TTL 1小时)
    await self.redis.setex(cache_key, 3600, json.dumps(result))
    
    return result

# ✅ 正确 — 数据变更时主动失效
async def update_analysis(self, project_id: uuid.UUID, data: dict) -> None:
    await self._save_analysis(project_id, data)
    await self.redis.delete(f"analysis:{project_id}")
```

### 9.3 批量操作

```python
# ✅ 正确 — 批量 Embedding
async def vectorize_chunks(self, chunks: list[str]) -> list[list[float]]:
    batch_size = 16
    all_embeddings = []
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        embeddings = await self.embedding_client.embed_batch(batch)
        all_embeddings.extend(embeddings)
    return all_embeddings

# ❌ 错误 — 逐条 Embedding
for chunk in chunks:
    embedding = await self.embedding_client.embed(chunk)  # ❌ N 次调用
```

```python
# ✅ 正确 — 批量插入
from sqlalchemy.dialects.postgresql import insert

stmt = insert(KnowledgeChunk).values([
    {"content": c.content, "embedding": c.embedding, "document_id": doc_id}
    for c in chunks
])
await db.execute(stmt)
await db.commit()

# ❌ 错误 — 循环逐条插入
for chunk in chunks:
    db.add(KnowledgeChunk(content=chunk.content, ...))
    await db.commit()  # ❌ N 次 commit
```

### 9.4 前端性能

```tsx
// ✅ 正确 — 大列表虚拟滚动
import { useVirtualizer } from "@tanstack/react-virtual"

// ✅ 正确 — 搜索防抖
import { useDebouncedCallback } from "use-debounce"

const debouncedSearch = useDebouncedCallback((value: string) => {
  setSearchQuery(value)
}, 300)

// ✅ 正确 — 图片/组件懒加载
import dynamic from "next/dynamic"
const HeavyChart = dynamic(() => import("./HeavyChart"), { ssr: false })

// ✅ 正确 — useMemo / useCallback 避免不必要渲染
const sortedItems = useMemo(
  () => items.sort((a, b) => b.updatedAt.localeCompare(a.updatedAt)),
  [items],
)
```

---

## 10. Git 提交与 Code Review 规范

### 10.1 提交格式

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**示例**:

```
feat(auth): implement JWT login and registration

- Add bcrypt password hashing
- Create JWT token generation with 30min expiry
- Add refresh token stored in Redis (7d TTL)
- Create get_current_user dependency

Closes #12
```

### 10.2 提交粒度

| 原则 | 说明 |
|------|------|
| 原子性 | 每次提交做一件事，能独立 revert |
| 可编译 | 每次提交后代码能通过 lint + build |
| 有意义 | 禁止 "fix"、"update"、"wip" 等无意义 message |

```bash
# ✅ 正确 — 原子提交
feat(auth): add user registration endpoint
feat(auth): add login endpoint
feat(auth): add JWT refresh logic
test(auth): add auth API integration tests

# ❌ 错误 — 混合提交
feat(auth): add registration, login, refresh, and all tests
```

### 10.3 Code Review Checklist

每个 PR 提交前，提交者**自检**:

**功能**:
- [ ] 需求完整实现
- [ ] 边界情况已处理 (空值、超长、并发)
- [ ] 错误码正确 (401/403/404/422)

**代码质量**:
- [ ] 函数不超过 50 行
- [ ] 命名清晰无歧义
- [ ] 无重复代码 (DRY)
- [ ] 类型提示完整
- [ ] 无 `TODO` / `FIXME` (或已创建 issue 跟踪)

**安全**:
- [ ] 无 SQL 拼接
- [ ] 无敏感信息泄露 (日志/响应)
- [ ] 输入已验证 (Pydantic)
- [ ] 权限已检查

**性能**:
- [ ] 无 N+1 查询
- [ ] 批量操作替代循环
- [ ] 热点数据有缓存

**测试**:
- [ ] 新代码有对应测试
- [ ] 测试命名清晰
- [ ] Mock 仅用于外部依赖

**i18n** (前端):
- [ ] 无硬编码文本
- [ ] 翻译 key 已添加到 zh.json + en.json

---

## 11. 禁止清单

> 以下做法在本项目中**严格禁止**。违反者需立即修复。

### Python 禁止

| 编号 | 禁止行为 | 替代方案 |
|------|---------|---------|
| P01 | `from module import *` | 显式导入需要的名称 |
| P02 | `except Exception: pass` (吞异常) | 至少 `logger.error(exc_info=True)` |
| P03 | `datetime.utcnow()` | `datetime.now(UTC)` |
| P04 | `print()` 调试 | `logger.debug()` |
| P05 | f-string 拼 SQL | SQLAlchemy 参数化查询 |
| P06 | `session.query()` (1.x 风格) | `select()` (2.0 风格) |
| P07 | 可变默认参数 `def f(x=[])` | `def f(x: list | None = None)` |
| P08 | 全局可变状态 | 依赖注入 / 函数参数 |
| P09 | 同步阻塞 I/O 在 async 函数中 | `asyncio.to_thread()` |
| P10 | Service 中抛 `HTTPException` | 抛 `BidAgentException` 子类 |
| P11 | API 层直接操作 ORM 模型 | 通过 Service 层间接访问 |
| P12 | 硬编码密钥/端口/URL | 环境变量 (`app.config`) |

### TypeScript 禁止

| 编号 | 禁止行为 | 替代方案 |
|------|---------|---------|
| T01 | `any` 类型 | `unknown` + 类型守卫 |
| T02 | 硬编码 UI 文本 | `next-intl` 翻译 |
| T03 | `console.log` 调试 | 开发环境 logger / 删除 |
| T04 | `as` 强制断言 (无验证) | 泛型 / 类型守卫 |
| T05 | 内联 `style={{}}` | Tailwind utility classes |
| T06 | Class 组件 | Function 组件 |
| T07 | 直接操作 DOM | React ref / state |
| T08 | 在组件中直接调 `fetch`/`axios` | 通过 Service + Hook 层 |
| T09 | 服务器数据存 Zustand | TanStack Query 管理 |
| T10 | `useEffect` 中发请求 | TanStack Query `useQuery` |

---

## 附录: 快速参考

### Python 文件模板

```python
"""模块说明。

详细描述 (可选)。
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.xxx import Xxx
from app.schemas.xxx import XxxCreate, XxxResponse


class XxxService:
    """Xxx 业务服务。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, xxx_id: uuid.UUID) -> Xxx:
        """根据 ID 获取资源。"""
        result = await self.db.execute(select(Xxx).where(Xxx.id == xxx_id))
        item = result.scalar_one_or_none()
        if item is None:
            raise NotFoundError(resource_type="Xxx", resource_id=str(xxx_id))
        return item
```

### React 组件模板

```tsx
"use client"

import { memo } from "react"
import { useTranslations } from "next-intl"

import { cn } from "@/lib/utils"

interface MyComponentProps {
  title: string
  isActive?: boolean
  className?: string
  onAction: () => void
}

function MyComponent({
  title,
  isActive = false,
  className,
  onAction,
}: MyComponentProps) {
  const t = useTranslations("myNamespace")

  return (
    <div className={cn("rounded-lg border p-4", { "border-primary": isActive }, className)}>
      <h3 className="text-lg font-semibold">{title}</h3>
      <button onClick={onAction}>{t("actionLabel")}</button>
    </div>
  )
}

export default memo(MyComponent)
```
