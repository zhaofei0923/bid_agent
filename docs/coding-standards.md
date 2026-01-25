# BidAgent 代码规范

## 目录
1. [通用规范](#通用规范)
2. [Python 代码规范](#python-代码规范)
3. [TypeScript 代码规范](#typescript-代码规范)
4. [Git 工作流](#git-工作流)
5. [代码审查](#代码审查)
6. [文档规范](#文档规范)

---

## 通用规范

### 命名约定

| 类型 | 约定 | 示例 |
|------|------|------|
| 文件名 | 小写下划线 (Python) / 小写短横线 (TS) | `credit_service.py`, `use-auth.ts` |
| 类名 | PascalCase | `CreditService`, `UserRepository` |
| 函数名 | snake_case (Python) / camelCase (TS) | `get_balance()`, `fetchUser()` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRIES`, `API_BASE_URL` |
| 变量 | snake_case (Python) / camelCase (TS) | `user_id`, `accessToken` |

### 注释原则

1. **解释为什么，而非是什么**
   ```python
   # 不好: 检查用户是否有效
   if user.is_active:
   
   # 好: 仅活跃用户可以发起生成请求，避免资源浪费
   if user.is_active:
   ```

2. **及时更新注释**
   - 代码变更时同步更新相关注释
   - 删除过时的注释

3. **复杂逻辑必须注释**
   ```python
   # 使用乐观锁防止并发扣费导致负余额
   # 如果更新行数为0，说明余额不足或被其他事务修改
   stmt = update(User).where(
       User.id == user_id,
       User.credits_balance >= amount  # 乐观锁条件
   ).values(credits_balance=User.credits_balance - amount)
   ```

---

## Python 代码规范

### 格式化工具

使用 **Ruff** 作为统一的格式化和检查工具：

```toml
# pyproject.toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
    "ARG",    # flake8-unused-arguments
    "SIM",    # flake8-simplify
]
ignore = [
    "E501",   # line too long (handled by formatter)
    "B008",   # do not perform function calls in argument defaults
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### 类型提示

**所有公共API必须有类型提示：**

```python
# ✅ 好
async def get_user_by_email(
    db: AsyncSession, 
    email: str
) -> User | None:
    """获取用户"""
    ...

# ❌ 不好
async def get_user_by_email(db, email):
    ...
```

**使用 `TypedDict` 定义复杂字典结构：**

```python
from typing import TypedDict, Optional, List

class TORAnalysis(TypedDict):
    project_title: str
    objectives: List[str]
    deliverables: List[dict]
    timeline: Optional[dict]
```

### 异常处理

**自定义业务异常：**

```python
# app/exceptions.py
from fastapi import HTTPException, status

class BidAgentException(Exception):
    """基础业务异常"""
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)

class InsufficientCreditsError(BidAgentException):
    """积分不足异常"""
    def __init__(self, required: int, available: int):
        self.required = required
        self.available = available
        super().__init__(
            message=f"积分不足: 需要 {required}, 可用 {available}",
            code="INSUFFICIENT_CREDITS"
        )

class DocumentNotFoundError(BidAgentException):
    """文档不存在异常"""
    def __init__(self, doc_id: str):
        super().__init__(
            message=f"文档不存在: {doc_id}",
            code="DOCUMENT_NOT_FOUND"
        )
```

**异常处理器：**

```python
# app/api/exception_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse
from app.exceptions import BidAgentException

async def bidagent_exception_handler(
    request: Request, 
    exc: BidAgentException
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        }
    )
```

### 日志规范

```python
import logging
from app.core.config import settings

# 配置结构化日志
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# 使用示例
logger.info(
    "用户登录成功",
    extra={"user_id": user.id, "ip": request.client.host}
)

logger.error(
    "LLM调用失败",
    extra={"model": model, "error": str(e)},
    exc_info=True
)
```

### 异步编程规范

```python
# ✅ 正确使用异步
async def process_documents(project_id: str) -> list[Document]:
    async with async_session() as db:
        documents = await get_project_documents(db, project_id)
        
        # 并行处理多个文档
        tasks = [parse_document(doc) for doc in documents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [r for r in results if not isinstance(r, Exception)]

# ❌ 避免阻塞异步循环
async def bad_example():
    # 不要在异步函数中使用阻塞IO
    with open("file.txt") as f:  # 阻塞!
        content = f.read()
    
    # 应该使用
    async with aiofiles.open("file.txt") as f:
        content = await f.read()
```

---

## TypeScript 代码规范

### ESLint配置

```javascript
// .eslintrc.js
module.exports = {
  extends: [
    "next/core-web-vitals",
    "plugin:@typescript-eslint/recommended",
    "prettier",
  ],
  rules: {
    "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
    "@typescript-eslint/explicit-function-return-type": "off",
    "@typescript-eslint/no-explicit-any": "warn",
    "react-hooks/exhaustive-deps": "warn",
    "prefer-const": "error",
    "no-console": ["warn", { allow: ["warn", "error"] }],
  },
}
```

### Prettier配置

```json
// .prettierrc
{
  "semi": false,
  "singleQuote": false,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 80,
  "plugins": ["prettier-plugin-tailwindcss"]
}
```

### React组件规范

**函数组件结构：**

```typescript
// src/components/projects/ProjectCard.tsx
"use client"

import { memo } from "react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import type { Project } from "@/types"

// 1. Props接口定义
interface ProjectCardProps {
  project: Project
  className?: string
  onClick?: (project: Project) => void
}

// 2. 组件实现
function ProjectCardComponent({ 
  project, 
  className,
  onClick 
}: ProjectCardProps) {
  const t = useTranslations("projects")
  
  // 3. Hooks调用
  // 4. 事件处理
  const handleClick = () => {
    onClick?.(project)
  }
  
  // 5. 渲染
  return (
    <div 
      className={cn("rounded-lg border p-4", className)}
      onClick={handleClick}
    >
      <h3 className="font-semibold">{project.name}</h3>
      <p className="text-sm text-muted-foreground">
        {t("status")}: {t(`statusLabels.${project.status}`)}
      </p>
    </div>
  )
}

// 6. 导出（可选memo）
export const ProjectCard = memo(ProjectCardComponent)
```

**自定义Hooks规范：**

```typescript
// src/hooks/useCredits.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "@/lib/api"
import type { CreditBalance, UsageStats } from "@/types"

// 查询键常量
const QUERY_KEYS = {
  balance: ["credits", "balance"] as const,
  usage: (days: number) => ["credits", "usage", days] as const,
  transactions: (page: number) => ["credits", "transactions", page] as const,
}

// 获取余额
export function useCredits() {
  return useQuery({
    queryKey: QUERY_KEYS.balance,
    queryFn: async (): Promise<CreditBalance> => {
      const response = await apiClient.get("/credits/balance")
      return response.data
    },
    staleTime: 30 * 1000, // 30秒缓存
  })
}

// 获取使用统计
export function useCreditsUsage(days: number = 30) {
  return useQuery({
    queryKey: QUERY_KEYS.usage(days),
    queryFn: async (): Promise<UsageStats> => {
      const response = await apiClient.get(`/credits/usage?days=${days}`)
      return response.data
    },
  })
}

// 充值Mutation
export function useRecharge() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (amount: number) => {
      const response = await apiClient.post("/credits/recharge", { amount })
      return response.data
    },
    onSuccess: () => {
      // 刷新余额
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.balance })
    },
  })
}
```

### 状态管理规范

**Zustand Store：**

```typescript
// src/stores/authStore.ts
import { create } from "zustand"
import { persist, createJSONStorage } from "zustand/middleware"
import type { User } from "@/types"

interface AuthState {
  user: User | null
  accessToken: string | null
  isAuthenticated: boolean
  
  // Actions
  setAuth: (user: User, token: string) => void
  logout: () => void
  updateUser: (updates: Partial<User>) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      
      setAuth: (user, token) => 
        set({ user, accessToken: token, isAuthenticated: true }),
      
      logout: () => 
        set({ user: null, accessToken: null, isAuthenticated: false }),
      
      updateUser: (updates) => 
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        })),
    }),
    {
      name: "auth-storage",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        accessToken: state.accessToken,
      }),
    }
  )
)
```

---

## Git 工作流

### 分支策略

```
main          ─────●─────────●─────────●─────── 生产环境
                   │         │         │
                   │         │         │
develop       ─────●────●────●────●────●─────── 开发主线
                        │         │
                        │         │
feature/xxx   ─────────●─────────●───────────── 功能分支
```

### 分支命名

| 类型 | 格式 | 示例 |
|------|------|------|
| 功能 | `feature/{module}-{description}` | `feature/auth-password-reset` |
| 修复 | `fix/{module}-{description}` | `fix/credits-negative-balance` |
| 热修复 | `hotfix/{description}` | `hotfix/login-crash` |
| 重构 | `refactor/{description}` | `refactor/api-error-handling` |

### Commit规范

采用 **Conventional Commits** 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type类型：**

| Type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug修复 |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响逻辑） |
| `refactor` | 重构 |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建/工具相关 |

**示例：**

```bash
# 新功能
feat(credits): 添加积分扣费服务

实现了积分扣费的核心逻辑，包括：
- 乐观锁防止并发问题
- 交易记录自动生成
- 余额不足异常处理

Closes #42

# Bug修复
fix(auth): 修复JWT过期后无法刷新的问题

当access_token过期时，refresh_token逻辑未正确执行。
根本原因是中间件未正确处理401响应。

Fixes #58

# 重构
refactor(api): 统一错误响应格式

将所有API错误响应统一为 {error: {code, message}} 格式
```

### PR规范

**PR标题格式：**
```
[M{milestone}] {type}: {description}
```

**示例：**
```
[M3] feat: 实现DeepSeek LangChain集成
[M6] fix: 修复积分并发扣费问题
```

**PR模板：**

```markdown
## 变更描述
<!-- 简要描述本PR的变更内容 -->

## 变更类型
- [ ] 新功能
- [ ] Bug修复
- [ ] 重构
- [ ] 文档
- [ ] 其他

## 关联Issue
<!-- 关联的Issue编号 -->
Closes #

## 测试情况
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试完成

## 检查清单
- [ ] 代码符合规范
- [ ] 添加了必要的注释
- [ ] 更新了相关文档
- [ ] 无安全风险
```

---

## 代码审查

### 审查清单

**功能正确性：**
- [ ] 代码实现了需求描述的功能
- [ ] 边界条件处理正确
- [ ] 错误处理完善

**代码质量：**
- [ ] 命名清晰有意义
- [ ] 函数职责单一
- [ ] 无重复代码
- [ ] 复杂度可接受

**安全性：**
- [ ] 无SQL注入风险
- [ ] 无XSS风险
- [ ] 敏感信息未泄露
- [ ] 权限检查正确

**性能：**
- [ ] 无N+1查询
- [ ] 适当使用缓存
- [ ] 无内存泄漏风险

**测试：**
- [ ] 有单元测试覆盖
- [ ] 测试用例有意义

### 审查评论规范

```
# 必须修改
🔴 **MUST**: 这里存在SQL注入风险，请使用参数化查询

# 建议修改
🟡 **SUGGEST**: 建议将这段逻辑抽取为独立函数，提高可读性

# 疑问
🔵 **QUESTION**: 这里为什么要用递归？循环是否更清晰？

# 赞赏
🟢 **NICE**: 这个设计很巧妙，很好地解决了并发问题
```

---

## 文档规范

### 代码文档

**Python Docstring (Google风格)：**

```python
def calculate_llm_credits(
    model: str,
    input_tokens: int,
    output_tokens: int
) -> int:
    """计算LLM调用消耗的积分。
    
    根据模型类型和token使用量计算积分消耗。
    
    Args:
        model: 模型名称，如 'deepseek-v3', 'deepseek-r1'
        input_tokens: 输入token数量
        output_tokens: 输出token数量
    
    Returns:
        消耗的积分数，最少为1
    
    Raises:
        ValueError: 当model不在支持列表中时
    
    Examples:
        >>> calculate_llm_credits('deepseek-v3', 1000, 500)
        1
        >>> calculate_llm_credits('deepseek-r1', 5000, 2000)
        8
    """
```

**TypeScript JSDoc：**

```typescript
/**
 * 格式化货币显示
 * 
 * @param amount - 金额数值
 * @param currency - 货币代码，默认USD
 * @param locale - 区域设置，默认en-US
 * @returns 格式化后的货币字符串
 * 
 * @example
 * ```ts
 * formatCurrency(1234.56) // "$1,234.56"
 * formatCurrency(1234.56, 'CNY', 'zh-CN') // "¥1,234.56"
 * ```
 */
export function formatCurrency(
  amount: number,
  currency: string = "USD",
  locale: string = "en-US"
): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
  }).format(amount)
}
```

### API文档

所有API必须在OpenAPI规范中定义，参见 [openapi.yaml](./api-contracts/openapi.yaml)。

### README模板

每个主要模块应有README说明：

```markdown
# 模块名称

## 概述
简要描述模块功能

## 安装
```bash
# 安装依赖
```

## 使用方法
```python
# 代码示例
```

## API参考
- `function_name()`: 功能说明

## 配置
| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| CONFIG_KEY | 说明 | default |

## 测试
```bash
# 运行测试
pytest tests/module_name/
```
```

---

## 附录

### 推荐的VS Code扩展

```json
// .vscode/extensions.json
{
  "recommendations": [
    "ms-vscode-remote.remote-wsl",
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "prisma.prisma",
    "ms-azuretools.vscode-docker"
  ]
}
```

### 编辑器配置

```json
// .vscode/settings.json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  },
  "python.analysis.typeCheckingMode": "basic",
  "typescript.preferences.importModuleSpecifier": "relative"
}
```
