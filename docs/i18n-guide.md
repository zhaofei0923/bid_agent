# BidAgent 多语言开发指南

## 目录
1. [概述](#概述)
2. [技术方案](#技术方案)
3. [前端国际化](#前端国际化)
4. [后端国际化](#后端国际化)
5. [数据库多语言](#数据库多语言)
6. [翻译工作流](#翻译工作流)
7. [最佳实践](#最佳实践)

---

## 概述

### 支持语言
| 语言 | 代码 | 优先级 | 阶段 |
|------|------|--------|------|
| 简体中文 | `zh` | P0 | MVP |
| English | `en` | P0 | MVP |
| Français | `fr` | P2 | Phase 2 |

### 多语言范围
- **用户界面 (UI)**: 所有前端文本
- **API错误消息**: 后端返回的错误提示
- **邮件模板**: 系统发送的邮件
- **生成内容**: LLM生成的标书内容（根据用户选择）
- **系统通知**: 推送通知、告警信息

---

## 技术方案

### 前端: next-intl

**选择理由：**
- 专为Next.js App Router设计
- 支持服务端渲染
- TypeScript支持完善
- 轻量级，无过度依赖

**安装：**
```bash
pnpm add next-intl
```

### 后端: 自定义方案

**选择理由：**
- 后端i18n需求简单（主要是错误消息）
- 无需引入重型框架
- 与Prompt模板管理统一

---

## 前端国际化

### 目录结构

```
frontend/src/
├── i18n/
│   ├── config.ts           # 配置文件
│   ├── request.ts          # 服务端请求
│   └── messages/
│       ├── zh.json         # 中文翻译
│       └── en.json         # 英文翻译
├── middleware.ts           # 语言检测中间件
└── app/
    └── [locale]/           # 动态语言路由
        ├── layout.tsx
        └── ...
```

### 配置文件

```typescript
// src/i18n/config.ts
export const locales = ["zh", "en"] as const
export type Locale = (typeof locales)[number]

export const defaultLocale: Locale = "zh"

export const localeNames: Record<Locale, string> = {
  zh: "中文",
  en: "English",
}

// 日期格式配置
export const dateFormats: Record<Locale, Intl.DateTimeFormatOptions> = {
  zh: { year: "numeric", month: "long", day: "numeric" },
  en: { year: "numeric", month: "long", day: "numeric" },
}
```

### 中间件配置

```typescript
// src/middleware.ts
import createMiddleware from "next-intl/middleware"
import { locales, defaultLocale } from "@/i18n/config"

export default createMiddleware({
  locales,
  defaultLocale,
  localePrefix: "always", // URL始终包含语言前缀
  localeDetection: true,  // 自动检测浏览器语言
})

export const config = {
  // 匹配所有路径，除了API、静态文件等
  matcher: ["/((?!api|_next|.*\\..*).*)"],
}
```

### 翻译文件结构

```json
// src/i18n/messages/zh.json
{
  "common": {
    "appName": "BidAgent",
    "loading": "加载中...",
    "error": "出错了",
    "save": "保存",
    "cancel": "取消",
    "confirm": "确认",
    "delete": "删除",
    "edit": "编辑",
    "create": "创建",
    "search": "搜索",
    "filter": "筛选",
    "export": "导出",
    "import": "导入"
  },
  "nav": {
    "dashboard": "工作台",
    "opportunities": "投标机会",
    "projects": "我的项目",
    "credits": "积分管理",
    "settings": "设置",
    "help": "帮助",
    "logout": "退出登录"
  },
  "auth": {
    "login": "登录",
    "register": "注册",
    "forgotPassword": "忘记密码",
    "email": "邮箱",
    "password": "密码",
    "confirmPassword": "确认密码",
    "fullName": "姓名",
    "loginSuccess": "登录成功",
    "registerSuccess": "注册成功，请查收验证邮件",
    "errors": {
      "invalidCredentials": "邮箱或密码错误",
      "emailExists": "该邮箱已注册",
      "weakPassword": "密码强度不足"
    }
  },
  "opportunities": {
    "title": "投标机会",
    "description": "浏览最新的多边开发银行投标机会",
    "table": {
      "title": "项目名称",
      "agency": "发布机构",
      "deadline": "截止日期",
      "budget": "预算",
      "status": "状态",
      "actions": "操作"
    },
    "status": {
      "active": "进行中",
      "closed": "已关闭",
      "awarded": "已中标"
    },
    "filters": {
      "agency": "机构",
      "country": "国家",
      "sector": "行业",
      "dateRange": "时间范围"
    }
  },
  "projects": {
    "title": "我的项目",
    "description": "管理您的投标项目",
    "createNew": "新建项目",
    "status": "状态",
    "statusLabels": {
      "draft": "草稿",
      "analyzing": "分析中",
      "generating": "生成中",
      "review": "待审核",
      "completed": "已完成"
    },
    "documents": "项目文档",
    "analysis": "分析结果",
    "generate": "生成标书",
    "history": "历史版本"
  },
  "generate": {
    "title": "标书生成",
    "notStarted": "点击下方按钮开始生成标书",
    "startGeneration": "开始生成",
    "steps": {
      "analyze_tor": "TOR分析",
      "extract_criteria": "评分标准提取",
      "create_outline": "大纲生成",
      "human_review": "人工审核",
      "generate_sections": "内容生成",
      "quality_check": "质量检查",
      "compile_document": "文档汇编"
    },
    "review": {
      "title": "审核大纲",
      "approve": "通过",
      "revise": "需要修改",
      "comments": "修改意见"
    },
    "completed": "生成完成",
    "viewDocument": "查看文档",
    "export": "导出"
  },
  "credits": {
    "balance": "积分余额",
    "recharge": "充值",
    "usage": "使用统计",
    "transactions": "交易明细",
    "status": {
      "healthy": "充足",
      "low": "偏低",
      "critical": "不足"
    },
    "lowBalanceWarning": "积分不足，请及时充值以继续使用",
    "usageChart": "最近30天使用趋势"
  },
  "errors": {
    "network": "网络错误，请检查网络连接",
    "unauthorized": "登录已过期，请重新登录",
    "forbidden": "没有权限执行此操作",
    "notFound": "资源不存在",
    "serverError": "服务器错误，请稍后重试",
    "insufficientCredits": "积分不足，请充值后继续"
  }
}
```

```json
// src/i18n/messages/en.json
{
  "common": {
    "appName": "BidAgent",
    "loading": "Loading...",
    "error": "Error",
    "save": "Save",
    "cancel": "Cancel",
    "confirm": "Confirm",
    "delete": "Delete",
    "edit": "Edit",
    "create": "Create",
    "search": "Search",
    "filter": "Filter",
    "export": "Export",
    "import": "Import"
  },
  "nav": {
    "dashboard": "Dashboard",
    "opportunities": "Opportunities",
    "projects": "My Projects",
    "credits": "Credits",
    "settings": "Settings",
    "help": "Help",
    "logout": "Logout"
  },
  "auth": {
    "login": "Login",
    "register": "Register",
    "forgotPassword": "Forgot Password",
    "email": "Email",
    "password": "Password",
    "confirmPassword": "Confirm Password",
    "fullName": "Full Name",
    "loginSuccess": "Login successful",
    "registerSuccess": "Registration successful, please check your email",
    "errors": {
      "invalidCredentials": "Invalid email or password",
      "emailExists": "Email already registered",
      "weakPassword": "Password is too weak"
    }
  },
  "opportunities": {
    "title": "Bid Opportunities",
    "description": "Browse latest opportunities from multilateral development banks",
    "table": {
      "title": "Title",
      "agency": "Agency",
      "deadline": "Deadline",
      "budget": "Budget",
      "status": "Status",
      "actions": "Actions"
    },
    "status": {
      "active": "Active",
      "closed": "Closed",
      "awarded": "Awarded"
    },
    "filters": {
      "agency": "Agency",
      "country": "Country",
      "sector": "Sector",
      "dateRange": "Date Range"
    }
  },
  "projects": {
    "title": "My Projects",
    "description": "Manage your bid projects",
    "createNew": "New Project",
    "status": "Status",
    "statusLabels": {
      "draft": "Draft",
      "analyzing": "Analyzing",
      "generating": "Generating",
      "review": "Pending Review",
      "completed": "Completed"
    },
    "documents": "Documents",
    "analysis": "Analysis",
    "generate": "Generate Bid",
    "history": "History"
  },
  "generate": {
    "title": "Bid Generation",
    "notStarted": "Click the button below to start generating your bid",
    "startGeneration": "Start Generation",
    "steps": {
      "analyze_tor": "TOR Analysis",
      "extract_criteria": "Criteria Extraction",
      "create_outline": "Outline Creation",
      "human_review": "Human Review",
      "generate_sections": "Content Generation",
      "quality_check": "Quality Check",
      "compile_document": "Document Compilation"
    },
    "review": {
      "title": "Review Outline",
      "approve": "Approve",
      "revise": "Request Revision",
      "comments": "Comments"
    },
    "completed": "Generation Complete",
    "viewDocument": "View Document",
    "export": "Export"
  },
  "credits": {
    "balance": "Credit Balance",
    "recharge": "Recharge",
    "usage": "Usage Statistics",
    "transactions": "Transactions",
    "status": {
      "healthy": "Healthy",
      "low": "Low",
      "critical": "Critical"
    },
    "lowBalanceWarning": "Low balance, please recharge to continue",
    "usageChart": "Usage Trend (Last 30 Days)"
  },
  "errors": {
    "network": "Network error, please check your connection",
    "unauthorized": "Session expired, please login again",
    "forbidden": "You don't have permission to perform this action",
    "notFound": "Resource not found",
    "serverError": "Server error, please try again later",
    "insufficientCredits": "Insufficient credits, please recharge"
  }
}
```

### 组件中使用

**客户端组件：**

```typescript
// src/components/projects/ProjectCard.tsx
"use client"

import { useTranslations } from "next-intl"

export function ProjectCard({ project }) {
  const t = useTranslations("projects")
  
  return (
    <div>
      <h3>{project.name}</h3>
      <span>{t("status")}: {t(`statusLabels.${project.status}`)}</span>
    </div>
  )
}
```

**服务端组件：**

```typescript
// src/app/[locale]/dashboard/page.tsx
import { getTranslations } from "next-intl/server"

export default async function DashboardPage() {
  const t = await getTranslations("nav")
  
  return (
    <h1>{t("dashboard")}</h1>
  )
}
```

**带变量的翻译：**

```json
// messages/zh.json
{
  "credits": {
    "balanceDisplay": "当前余额: {balance} 积分",
    "consumedToday": "今日已消耗 {amount} 积分"
  }
}
```

```typescript
const t = useTranslations("credits")
t("balanceDisplay", { balance: 1000 }) // "当前余额: 1000 积分"
```

**复数形式：**

```json
// messages/en.json
{
  "projects": {
    "count": "{count, plural, =0 {No projects} =1 {1 project} other {# projects}}"
  }
}
```

```typescript
t("count", { count: 5 }) // "5 projects"
```

### 日期和数字格式化

```typescript
// src/components/common/FormattedDate.tsx
"use client"

import { useFormatter, useLocale } from "next-intl"

export function FormattedDate({ date }: { date: Date | string }) {
  const format = useFormatter()
  const dateObj = typeof date === "string" ? new Date(date) : date
  
  return (
    <time dateTime={dateObj.toISOString()}>
      {format.dateTime(dateObj, {
        year: "numeric",
        month: "long",
        day: "numeric",
      })}
    </time>
  )
}

export function FormattedCurrency({ 
  amount, 
  currency = "USD" 
}: { 
  amount: number
  currency?: string 
}) {
  const format = useFormatter()
  
  return (
    <span>
      {format.number(amount, {
        style: "currency",
        currency,
      })}
    </span>
  )
}
```

---

## 后端国际化

### 错误消息国际化

```python
# app/i18n/messages.py
from typing import Dict
from enum import Enum

class ErrorCode(str, Enum):
    INSUFFICIENT_CREDITS = "INSUFFICIENT_CREDITS"
    DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    VALIDATION_ERROR = "VALIDATION_ERROR"

# 错误消息翻译
ERROR_MESSAGES: Dict[str, Dict[ErrorCode, str]] = {
    "zh": {
        ErrorCode.INSUFFICIENT_CREDITS: "积分不足，需要 {required} 积分，当前余额 {available} 积分",
        ErrorCode.DOCUMENT_NOT_FOUND: "文档不存在: {doc_id}",
        ErrorCode.INVALID_CREDENTIALS: "邮箱或密码错误",
        ErrorCode.UNAUTHORIZED: "请先登录",
        ErrorCode.FORBIDDEN: "没有权限执行此操作",
        ErrorCode.VALIDATION_ERROR: "数据验证失败: {detail}",
    },
    "en": {
        ErrorCode.INSUFFICIENT_CREDITS: "Insufficient credits. Required: {required}, Available: {available}",
        ErrorCode.DOCUMENT_NOT_FOUND: "Document not found: {doc_id}",
        ErrorCode.INVALID_CREDENTIALS: "Invalid email or password",
        ErrorCode.UNAUTHORIZED: "Please login first",
        ErrorCode.FORBIDDEN: "You don't have permission to perform this action",
        ErrorCode.VALIDATION_ERROR: "Validation failed: {detail}",
    },
}

def get_error_message(
    code: ErrorCode, 
    locale: str = "zh",
    **kwargs
) -> str:
    """获取本地化的错误消息"""
    messages = ERROR_MESSAGES.get(locale, ERROR_MESSAGES["en"])
    template = messages.get(code, str(code))
    return template.format(**kwargs)
```

### 请求语言检测

```python
# app/api/deps.py
from fastapi import Request, Header
from typing import Optional

def get_locale(
    request: Request,
    accept_language: Optional[str] = Header(None),
) -> str:
    """
    获取请求的语言偏好
    优先级: 
    1. URL参数 ?locale=xx
    2. Accept-Language头
    3. 默认中文
    """
    # URL参数
    if "locale" in request.query_params:
        locale = request.query_params["locale"]
        if locale in ["zh", "en"]:
            return locale
    
    # Accept-Language头
    if accept_language:
        # 简单解析，实际可用 accept-language-parser
        if "zh" in accept_language.lower():
            return "zh"
        if "en" in accept_language.lower():
            return "en"
    
    return "zh"
```

### 在异常中使用

```python
# app/exceptions.py
from app.i18n.messages import get_error_message, ErrorCode

class InsufficientCreditsError(BidAgentException):
    def __init__(self, required: int, available: int, locale: str = "zh"):
        self.required = required
        self.available = available
        message = get_error_message(
            ErrorCode.INSUFFICIENT_CREDITS,
            locale,
            required=required,
            available=available
        )
        super().__init__(message=message, code=ErrorCode.INSUFFICIENT_CREDITS)
```

### Prompt模板多语言

```python
# app/agents/prompts/prompt_manager.py
import yaml
from pathlib import Path
from typing import Dict, Any
from functools import lru_cache

PROMPTS_DIR = Path(__file__).parent / "templates"

@lru_cache(maxsize=100)
def load_prompt(name: str, locale: str = "zh") -> Dict[str, Any]:
    """加载Prompt模板"""
    file_path = PROMPTS_DIR / locale / f"{name}.yaml"
    
    if not file_path.exists():
        # 回退到英文
        file_path = PROMPTS_DIR / "en" / f"{name}.yaml"
    
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class PromptTemplate:
    def __init__(self, data: Dict[str, Any]):
        self.template = data["template"]
        self.input_variables = data.get("input_variables", [])
        self.description = data.get("description", "")
    
    def format(self, **kwargs) -> str:
        return self.template.format(**kwargs)


class PromptManager:
    def __init__(self):
        self._cache: Dict[str, PromptTemplate] = {}
    
    def get(self, name: str, locale: str = "zh") -> PromptTemplate:
        cache_key = f"{name}_{locale}"
        
        if cache_key not in self._cache:
            data = load_prompt(name, locale)
            self._cache[cache_key] = PromptTemplate(data)
        
        return self._cache[cache_key]


# 全局实例
prompt_manager = PromptManager()
```

**Prompt模板文件：**

```yaml
# prompts/templates/zh/tor_analysis.yaml
description: TOR文档分析提示词
template: |
  你是一位资深的国际咨询顾问，擅长分析投标文件。
  
  ## 任务
  分析以下任务书(TOR)文档，提取关键信息。
  
  ## TOR文档内容
  {tor_content}
  
  ## 提取要求
  请提取以下信息，以JSON格式返回：
  1. project_title: 项目名称
  2. objectives: 项目目标（数组）
  ...

input_variables:
  - tor_content
```

```yaml
# prompts/templates/en/tor_analysis.yaml
description: TOR Document Analysis Prompt
template: |
  You are a senior international consultant specializing in bid document analysis.
  
  ## Task
  Analyze the following Terms of Reference (TOR) document and extract key information.
  
  ## TOR Content
  {tor_content}
  
  ## Extraction Requirements
  Please extract the following information in JSON format:
  1. project_title: Project title
  2. objectives: Project objectives (array)
  ...

input_variables:
  - tor_content
```

---

## 数据库多语言

### 翻译表设计

对于需要多语言的内容（如系统通知模板），使用翻译表：

```sql
-- 翻译表
CREATE TABLE translations (
    id UUID PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,  -- 'notification_template', 'email_template'等
    entity_id UUID NOT NULL,
    locale VARCHAR(10) NOT NULL,
    field_name VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(entity_type, entity_id, locale, field_name)
);

CREATE INDEX idx_translations_entity ON translations(entity_type, entity_id);
```

### 使用示例

```python
# app/models/translation.py
from sqlalchemy import Column, String, Text, UniqueConstraint
from app.database import Base

class Translation(Base):
    __tablename__ = "translations"
    
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=False)
    locale = Column(String(10), nullable=False)
    field_name = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    
    __table_args__ = (
        UniqueConstraint(
            'entity_type', 'entity_id', 'locale', 'field_name',
            name='uq_translation'
        ),
    )


# app/services/translation_service.py
async def get_translated_content(
    db: AsyncSession,
    entity_type: str,
    entity_id: str,
    field_name: str,
    locale: str,
    fallback_locale: str = "en"
) -> Optional[str]:
    """获取翻译内容，支持回退"""
    result = await db.execute(
        select(Translation.content)
        .where(
            Translation.entity_type == entity_type,
            Translation.entity_id == entity_id,
            Translation.field_name == field_name,
            Translation.locale == locale
        )
    )
    content = result.scalar_one_or_none()
    
    if content is None and locale != fallback_locale:
        # 回退到默认语言
        result = await db.execute(
            select(Translation.content)
            .where(
                Translation.entity_type == entity_type,
                Translation.entity_id == entity_id,
                Translation.field_name == field_name,
                Translation.locale == fallback_locale
            )
        )
        content = result.scalar_one_or_none()
    
    return content
```

---

## 翻译工作流

### 翻译键管理

1. **使用有意义的键名**
   ```
   ✅ auth.errors.invalidCredentials
   ❌ auth.err1
   ```

2. **保持层级结构**
   ```json
   {
     "模块": {
       "子模块": {
         "具体文本": "翻译"
       }
     }
   }
   ```

3. **使用翻译检查脚本**

```typescript
// scripts/check-translations.ts
import zh from "../src/i18n/messages/zh.json"
import en from "../src/i18n/messages/en.json"

function getAllKeys(obj: any, prefix = ""): string[] {
  return Object.keys(obj).flatMap((key) => {
    const path = prefix ? `${prefix}.${key}` : key
    return typeof obj[key] === "object"
      ? getAllKeys(obj[key], path)
      : [path]
  })
}

const zhKeys = new Set(getAllKeys(zh))
const enKeys = new Set(getAllKeys(en))

// 检查缺失的键
const missingInEn = [...zhKeys].filter((k) => !enKeys.has(k))
const missingInZh = [...enKeys].filter((k) => !zhKeys.has(k))

if (missingInEn.length) {
  console.error("Missing in EN:", missingInEn)
}
if (missingInZh.length) {
  console.error("Missing in ZH:", missingInZh)
}

process.exit(missingInEn.length + missingInZh.length > 0 ? 1 : 0)
```

### CI检查

```yaml
# .github/workflows/ci.yml
jobs:
  translation-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check translations
        run: |
          cd frontend
          npx ts-node scripts/check-translations.ts
```

---

## 最佳实践

### 1. 避免硬编码文本

```typescript
// ❌ 不好
<button>Submit</button>

// ✅ 好
<button>{t("common.submit")}</button>
```

### 2. 处理动态内容

```typescript
// ❌ 不好: 拼接字符串
`Welcome, ${user.name}!`

// ✅ 好: 使用变量
t("welcome", { name: user.name })
// messages: { "welcome": "欢迎, {name}!" }
```

### 3. 注意语序差异

中英文语序不同，避免拆分句子：

```typescript
// ❌ 不好: 拆分句子
<>
  {t("you_have")} {count} {t("items")}
</>

// ✅ 好: 完整句子
t("item_count", { count })
// zh: "您有 {count} 个项目"
// en: "You have {count} items"
```

### 4. 处理复数

```json
// en.json
{
  "items": "{count, plural, =0 {No items} =1 {1 item} other {# items}}"
}

// zh.json (中文通常不需要复数形式)
{
  "items": "{count} 个项目"
}
```

### 5. 日期和货币本地化

始终使用格式化函数，不要手动拼接：

```typescript
// ❌ 不好
`${date.getMonth()}/${date.getDate()}/${date.getFullYear()}`

// ✅ 好
format.dateTime(date, { dateStyle: "medium" })
```

### 6. RTL支持准备

虽然当前不支持RTL语言，但保持良好习惯：

```css
/* 使用逻辑属性 */
.container {
  /* ❌ */
  margin-left: 1rem;
  
  /* ✅ */
  margin-inline-start: 1rem;
}
```

### 7. 翻译上下文

提供足够的上下文给翻译者：

```json
{
  "_comments": {
    "auth.login": "登录按钮文本",
    "auth.login_action": "动作描述，如 '正在登录...'"
  },
  "auth": {
    "login": "登录",
    "login_action": "正在登录..."
  }
}
```

---

## 附录

### 常用翻译资源

| 资源 | 说明 |
|------|------|
| [next-intl文档](https://next-intl-docs.vercel.app/) | 官方文档 |
| [ICU Message Format](https://unicode-org.github.io/icu/userguide/format_parse/messages/) | 消息格式规范 |
| [CLDR](https://cldr.unicode.org/) | Unicode通用本地化数据 |

### 翻译管理工具推荐

- **Crowdin**: 专业翻译管理平台
- **Lokalise**: 支持Git集成
- **Weblate**: 开源自托管方案
