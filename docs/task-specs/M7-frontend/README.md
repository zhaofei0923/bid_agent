# M7 - 前端开发任务规格书

## 概述
| 属性 | 值 |
|------|-----|
| 里程碑 | M7 - Frontend |
| 周期 | Week 10-11 |
| 任务总数 | 14 |
| Opus 4.5 任务 | 2 |
| Mini-Agent 任务 | 12 |

## 目标
- 完成所有核心页面
- 实现响应式设计
- 完成多语言支持
- 优化用户体验

---

## 任务列表

### M7-01: 前端架构复审 (Opus 4.5)
**优先级**: P0  
**预估时间**: 2小时  
**执行者**: Opus 4.5

#### 描述
复审前端架构设计，确保可扩展性。

#### 复审要点
1. 目录结构合理性
2. 状态管理方案
3. API调用模式
4. 组件复用性
5. 性能优化策略

#### 目录结构
```
frontend/src/
├── app/                       # Next.js App Router
│   ├── [locale]/              # 多语言路由
│   │   ├── (auth)/            # 认证相关页面组
│   │   │   ├── login/
│   │   │   ├── register/
│   │   │   └── forgot-password/
│   │   ├── (dashboard)/       # 主面板页面组
│   │   │   ├── layout.tsx     # 仪表盘布局
│   │   │   ├── page.tsx       # 首页/概览
│   │   │   ├── opportunities/
│   │   │   ├── projects/
│   │   │   ├── credits/
│   │   │   └── settings/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── api/                   # API路由 (BFF)
│   └── globals.css
├── components/
│   ├── ui/                    # shadcn/ui 组件
│   ├── layout/                # 布局组件
│   ├── forms/                 # 表单组件
│   ├── opportunities/         # 机会相关组件
│   ├── projects/              # 项目相关组件
│   └── credits/               # 积分相关组件
├── hooks/                     # 自定义Hooks
├── lib/                       # 工具函数
├── services/                  # API服务层
├── stores/                    # Zustand存储
├── types/                     # TypeScript类型
├── i18n/                      # 多语言配置
│   ├── messages/
│   │   ├── en.json
│   │   └── zh.json
│   └── request.ts
└── middleware.ts              # 多语言中间件
```

#### 验收标准
- [ ] 架构设计文档更新
- [ ] 目录结构确认
- [ ] 关键技术决策记录

---

### M7-02: 全局布局组件 (Mini-Agent)
**优先级**: P0  
**预估时间**: 3小时  
**执行者**: Mini-Agent

#### 描述
实现仪表盘全局布局。

#### 代码实现
```typescript
// src/app/[locale]/(dashboard)/layout.tsx
import { Sidebar } from "@/components/layout/Sidebar"
import { TopBar } from "@/components/layout/TopBar"
import { Toaster } from "@/components/ui/toaster"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* 侧边栏 */}
      <Sidebar />
      
      {/* 主内容区 */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* 顶部栏 */}
        <TopBar />
        
        {/* 页面内容 */}
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
      
      {/* Toast通知 */}
      <Toaster />
    </div>
  )
}


// src/components/layout/Sidebar.tsx
"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import {
  Home,
  Search,
  FolderOpen,
  Coins,
  Settings,
  HelpCircle,
  LogOut,
} from "lucide-react"
import { CreditBalance } from "@/components/credits/CreditBalance"
import { useAuth } from "@/hooks/useAuth"

const navigation = [
  { name: "dashboard", href: "/dashboard", icon: Home },
  { name: "opportunities", href: "/dashboard/opportunities", icon: Search },
  { name: "projects", href: "/dashboard/projects", icon: FolderOpen },
  { name: "credits", href: "/dashboard/credits", icon: Coins },
  { name: "settings", href: "/dashboard/settings", icon: Settings },
]

export function Sidebar() {
  const t = useTranslations("nav")
  const pathname = usePathname()
  const { logout } = useAuth()
  
  return (
    <aside className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-gray-200 dark:border-gray-700">
        <Link href="/dashboard" className="flex items-center space-x-2">
          <span className="text-2xl font-bold text-primary">BidAgent</span>
        </Link>
      </div>
      
      {/* 导航菜单 */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname.includes(item.href)
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
              )}
            >
              <item.icon className="w-5 h-5 mr-3" />
              {t(item.name)}
            </Link>
          )
        })}
      </nav>
      
      {/* 积分余额 */}
      <div className="px-3 py-4 border-t border-gray-200 dark:border-gray-700">
        <CreditBalance compact />
      </div>
      
      {/* 底部操作 */}
      <div className="px-3 py-4 border-t border-gray-200 dark:border-gray-700 space-y-1">
        <Link
          href="/help"
          className="flex items-center px-3 py-2 rounded-md text-sm text-gray-600 hover:bg-gray-100"
        >
          <HelpCircle className="w-5 h-5 mr-3" />
          {t("help")}
        </Link>
        <button
          onClick={logout}
          className="w-full flex items-center px-3 py-2 rounded-md text-sm text-red-600 hover:bg-red-50"
        >
          <LogOut className="w-5 h-5 mr-3" />
          {t("logout")}
        </button>
      </div>
    </aside>
  )
}


// src/components/layout/TopBar.tsx
"use client"

import { useTranslations } from "next-intl"
import { Bell, User, Globe } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { usePathname, useRouter } from "next/navigation"

export function TopBar() {
  const t = useTranslations("common")
  const router = useRouter()
  const pathname = usePathname()
  
  const switchLocale = (locale: string) => {
    const segments = pathname.split("/")
    segments[1] = locale
    router.push(segments.join("/"))
  }
  
  return (
    <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-6">
      {/* 搜索框 */}
      <div className="flex-1 max-w-md">
        {/* 可选: 全局搜索 */}
      </div>
      
      {/* 右侧工具栏 */}
      <div className="flex items-center space-x-4">
        {/* 语言切换 */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <Globe className="w-5 h-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => switchLocale("zh")}>
              中文
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => switchLocale("en")}>
              English
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        
        {/* 通知 */}
        <Button variant="ghost" size="icon">
          <Bell className="w-5 h-5" />
        </Button>
        
        {/* 用户菜单 */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <User className="w-5 h-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>{t("profile")}</DropdownMenuItem>
            <DropdownMenuItem>{t("settings")}</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
```

#### 验收标准
- [ ] 响应式侧边栏
- [ ] 顶部导航栏
- [ ] 语言切换
- [ ] 移动端适配

#### 依赖
- M0-02

---

### M7-03: Dashboard首页 (Mini-Agent)
**优先级**: P1  
**预估时间**: 3小时  
**执行者**: Mini-Agent

#### 描述
实现仪表盘首页概览。

#### 验收标准
- [ ] 统计卡片
- [ ] 最近项目
- [ ] 最新机会
- [ ] 快速操作

#### 依赖
- M7-02

---

### M7-04: 机会列表页 (Mini-Agent)
**优先级**: P0  
**预估时间**: 4小时  
**执行者**: Mini-Agent

#### 描述
实现投标机会列表页面。

#### 代码实现
```typescript
// src/app/[locale]/(dashboard)/opportunities/page.tsx
import { Suspense } from "react"
import { OpportunitiesTable } from "@/components/opportunities/OpportunitiesTable"
import { OpportunitiesFilters } from "@/components/opportunities/OpportunitiesFilters"
import { PageHeader } from "@/components/layout/PageHeader"
import { Skeleton } from "@/components/ui/skeleton"

export default function OpportunitiesPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="opportunities.title"
        description="opportunities.description"
      />
      
      <OpportunitiesFilters />
      
      <Suspense fallback={<OpportunitiesTableSkeleton />}>
        <OpportunitiesTable />
      </Suspense>
    </div>
  )
}

function OpportunitiesTableSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-16 w-full" />
      ))}
    </div>
  )
}


// src/components/opportunities/OpportunitiesTable.tsx
"use client"

import { useOpportunities } from "@/hooks/useOpportunities"
import { useTranslations } from "next-intl"
import { formatDate, formatCurrency } from "@/lib/utils"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Eye, FolderPlus } from "lucide-react"
import { useRouter } from "next/navigation"
import { Pagination } from "@/components/ui/pagination"

export function OpportunitiesTable() {
  const t = useTranslations("opportunities")
  const router = useRouter()
  const { 
    opportunities, 
    total, 
    page, 
    setPage,
    isLoading 
  } = useOpportunities()
  
  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive"> = {
      active: "default",
      closed: "secondary",
      awarded: "destructive",
    }
    return <Badge variant={variants[status] || "default"}>{t(`status.${status}`)}</Badge>
  }
  
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>{t("table.title")}</TableHead>
            <TableHead>{t("table.agency")}</TableHead>
            <TableHead>{t("table.deadline")}</TableHead>
            <TableHead>{t("table.budget")}</TableHead>
            <TableHead>{t("table.status")}</TableHead>
            <TableHead className="text-right">{t("table.actions")}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {opportunities.map((opp) => (
            <TableRow key={opp.id}>
              <TableCell className="font-medium max-w-md">
                <div className="truncate">{opp.title}</div>
                <div className="text-sm text-gray-500">{opp.reference_number}</div>
              </TableCell>
              <TableCell>
                <Badge variant="outline">{opp.agency}</Badge>
              </TableCell>
              <TableCell>{formatDate(opp.deadline)}</TableCell>
              <TableCell>
                {opp.estimated_budget 
                  ? formatCurrency(opp.estimated_budget, opp.currency)
                  : "-"
                }
              </TableCell>
              <TableCell>{getStatusBadge(opp.status)}</TableCell>
              <TableCell className="text-right space-x-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => router.push(`/dashboard/opportunities/${opp.id}`)}
                >
                  <Eye className="w-4 h-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => router.push(`/dashboard/projects/new?opportunity=${opp.id}`)}
                >
                  <FolderPlus className="w-4 h-4" />
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      
      <div className="p-4 border-t">
        <Pagination
          total={total}
          page={page}
          pageSize={20}
          onPageChange={setPage}
        />
      </div>
    </div>
  )
}
```

#### 验收标准
- [ ] 列表展示
- [ ] 分页功能
- [ ] 筛选过滤
- [ ] 创建项目入口

#### 依赖
- M2-06, M7-02

---

### M7-05: 机会详情页 (Mini-Agent)
**优先级**: P1  
**预估时间**: 3小时  
**执行者**: Mini-Agent

#### 描述
实现投标机会详情页面。

#### 验收标准
- [ ] 基本信息展示
- [ ] 文档下载
- [ ] 时间线显示
- [ ] 创建项目按钮

#### 依赖
- M7-04

---

### M7-06: 项目列表页 (Mini-Agent)
**优先级**: P0  
**预估时间**: 3小时  
**执行者**: Mini-Agent

#### 描述
实现用户项目列表页面。

#### 验收标准
- [ ] 项目卡片
- [ ] 状态筛选
- [ ] 搜索功能
- [ ] 排序功能

#### 依赖
- M7-02

---

### M7-07: 项目创建流程 (Opus 4.5)
**优先级**: P0  
**预估时间**: 4小时  
**执行者**: Opus 4.5

#### 描述
设计并实现项目创建多步骤流程。

#### 流程设计
```
Step 1: 选择机会 / 手动创建
  └── 从机会列表选择
  └── 或手动输入项目信息

Step 2: 上传文档
  └── TOR (必须)
  └── 评标标准 (可选)
  └── 其他参考文档

Step 3: 确认信息
  └── 预览项目详情
  └── 预估积分消耗
  └── 创建项目
```

#### 验收标准
- [ ] 多步骤表单
- [ ] 文档上传
- [ ] 表单验证
- [ ] 创建成功跳转

#### 依赖
- M7-06

---

### M7-08: 项目详情页 (Mini-Agent)
**优先级**: P0  
**预估时间**: 4小时  
**执行者**: Mini-Agent

#### 描述
实现项目详情和操作页面。

#### 代码实现
```typescript
// src/app/[locale]/(dashboard)/projects/[id]/page.tsx
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ProjectHeader } from "@/components/projects/ProjectHeader"
import { ProjectDocuments } from "@/components/projects/ProjectDocuments"
import { ProjectAnalysis } from "@/components/projects/ProjectAnalysis"
import { ProjectGenerate } from "@/components/projects/ProjectGenerate"
import { ProjectHistory } from "@/components/projects/ProjectHistory"

interface Props {
  params: { id: string }
}

export default async function ProjectDetailPage({ params }: Props) {
  return (
    <div className="space-y-6">
      <ProjectHeader projectId={params.id} />
      
      <Tabs defaultValue="documents" className="w-full">
        <TabsList>
          <TabsTrigger value="documents">文档</TabsTrigger>
          <TabsTrigger value="analysis">分析</TabsTrigger>
          <TabsTrigger value="generate">生成</TabsTrigger>
          <TabsTrigger value="history">历史</TabsTrigger>
        </TabsList>
        
        <TabsContent value="documents" className="mt-4">
          <ProjectDocuments projectId={params.id} />
        </TabsContent>
        
        <TabsContent value="analysis" className="mt-4">
          <ProjectAnalysis projectId={params.id} />
        </TabsContent>
        
        <TabsContent value="generate" className="mt-4">
          <ProjectGenerate projectId={params.id} />
        </TabsContent>
        
        <TabsContent value="history" className="mt-4">
          <ProjectHistory projectId={params.id} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
```

#### 验收标准
- [ ] Tab页切换
- [ ] 文档列表
- [ ] 分析结果
- [ ] 生成操作

#### 依赖
- M7-07

---

### M7-09: 文档上传组件 (Mini-Agent)
**优先级**: P0  
**预估时间**: 3小时  
**执行者**: Mini-Agent

#### 描述
实现拖拽文档上传组件。

#### 验收标准
- [ ] 拖拽上传
- [ ] 文件类型检查
- [ ] 上传进度
- [ ] 预览功能

#### 依赖
- M4-02

---

### M7-10: 标书生成界面 (Mini-Agent)
**优先级**: P0  
**预估时间**: 4小时  
**执行者**: Mini-Agent

#### 描述
实现标书生成交互界面。

#### 代码实现
```typescript
// src/components/projects/ProjectGenerate.tsx
"use client"

import { useState, useEffect } from "react"
import { useTranslations } from "next-intl"
import { useGenerationStatus, useStartGeneration, useSubmitReview } from "@/hooks/useGeneration"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { 
  Play, 
  Pause, 
  CheckCircle, 
  AlertCircle,
  Loader2 
} from "lucide-react"
import { OutlineReview } from "./OutlineReview"

interface Props {
  projectId: string
}

const STEPS = [
  { key: "analyze_tor", label: "TOR分析", progress: 20 },
  { key: "extract_criteria", label: "评分标准", progress: 35 },
  { key: "create_outline", label: "大纲生成", progress: 50 },
  { key: "human_review", label: "人工审核", progress: 60 },
  { key: "generate_sections", label: "内容生成", progress: 80 },
  { key: "quality_check", label: "质量检查", progress: 90 },
  { key: "compile_document", label: "文档汇编", progress: 100 },
]

export function ProjectGenerate({ projectId }: Props) {
  const t = useTranslations("generate")
  const { data: status, refetch } = useGenerationStatus(projectId)
  const startGeneration = useStartGeneration()
  const submitReview = useSubmitReview()
  
  // 轮询状态
  useEffect(() => {
    if (status?.status === "running") {
      const interval = setInterval(refetch, 3000)
      return () => clearInterval(interval)
    }
  }, [status?.status, refetch])
  
  const currentStepIndex = STEPS.findIndex(s => s.key === status?.current_step)
  const progress = currentStepIndex >= 0 ? STEPS[currentStepIndex].progress : 0
  
  const handleStart = async () => {
    await startGeneration.mutateAsync({ projectId })
  }
  
  const handleReviewSubmit = async (decision: string, comments: string) => {
    await submitReview.mutateAsync({
      projectId,
      decision,
      comments,
    })
    refetch()
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("title")}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* 状态指示 */}
        {!status && (
          <div className="text-center py-8">
            <p className="text-gray-500 mb-4">{t("notStarted")}</p>
            <Button onClick={handleStart} disabled={startGeneration.isPending}>
              {startGeneration.isPending ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Play className="w-4 h-4 mr-2" />
              )}
              {t("startGeneration")}
            </Button>
          </div>
        )}
        
        {status?.status === "running" && (
          <>
            {/* 进度条 */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>{STEPS[currentStepIndex]?.label || "处理中..."}</span>
                <span>{progress}%</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>
            
            {/* 步骤列表 */}
            <div className="space-y-2">
              {STEPS.map((step, index) => (
                <div 
                  key={step.key}
                  className={`flex items-center space-x-2 text-sm ${
                    index < currentStepIndex 
                      ? "text-green-600" 
                      : index === currentStepIndex
                      ? "text-blue-600 font-medium"
                      : "text-gray-400"
                  }`}
                >
                  {index < currentStepIndex ? (
                    <CheckCircle className="w-4 h-4" />
                  ) : index === currentStepIndex ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border-2 border-current" />
                  )}
                  <span>{step.label}</span>
                </div>
              ))}
            </div>
          </>
        )}
        
        {/* 等待审核 */}
        {status?.waiting_for_review && (
          <Alert>
            <AlertDescription>
              <OutlineReview
                data={status.review_data}
                onSubmit={handleReviewSubmit}
              />
            </AlertDescription>
          </Alert>
        )}
        
        {/* 错误信息 */}
        {status?.errors?.length > 0 && (
          <Alert variant="destructive">
            <AlertCircle className="w-4 h-4" />
            <AlertDescription>
              {status.errors.join(", ")}
            </AlertDescription>
          </Alert>
        )}
        
        {/* 完成 */}
        {status?.status === "completed" && (
          <div className="text-center py-8">
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
            <p className="text-lg font-medium mb-4">{t("completed")}</p>
            <div className="space-x-2">
              <Button variant="outline">
                {t("viewDocument")}
              </Button>
              <Button>
                {t("export")}
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
```

#### 验收标准
- [ ] 启动生成
- [ ] 进度显示
- [ ] 人工审核交互
- [ ] 结果展示

#### 依赖
- M5-10, M7-08

---

### M7-11: 大纲审核组件 (Mini-Agent)
**优先级**: P0  
**预估时间**: 2小时  
**执行者**: Mini-Agent

#### 描述
实现大纲人工审核组件。

#### 验收标准
- [ ] 大纲展示
- [ ] 编辑功能
- [ ] 批准/驳回
- [ ] 修改建议

#### 依赖
- M7-10

---

### M7-12: 积分管理页面 (Mini-Agent)
**优先级**: P1  
**预估时间**: 3小时  
**执行者**: Mini-Agent

#### 描述
实现积分管理完整页面。

#### 验收标准
- [ ] 余额展示
- [ ] 使用统计
- [ ] 交易明细
- [ ] 充值入口

#### 依赖
- M6-06

---

### M7-13: 设置页面 (Mini-Agent)
**优先级**: P2  
**预估时间**: 2小时  
**执行者**: Mini-Agent

#### 描述
实现用户设置页面。

#### 验收标准
- [ ] 个人信息
- [ ] 密码修改
- [ ] 语言偏好
- [ ] 通知设置

#### 依赖
- M1-05

---

### M7-14: 错误边界与空状态 (Mini-Agent)
**优先级**: P1  
**预估时间**: 2小时  
**执行者**: Mini-Agent

#### 描述
实现全局错误处理和空状态组件。

#### 验收标准
- [ ] Error Boundary
- [ ] 空状态组件
- [ ] 404页面
- [ ] 500页面

#### 依赖
- M7-02

---

## 里程碑检查点

### 完成标准
- [ ] 所有核心页面可访问
- [ ] 响应式适配完成
- [ ] 多语言切换正常
- [ ] 用户流程顺畅

### 交付物
1. 完整的前端应用
2. 组件库文档
3. 页面截图/录屏

---

## UI/UX规范

### 颜色方案
```css
:root {
  --primary: 221.2 83.2% 53.3%;       /* 主色 蓝色 */
  --primary-foreground: 210 40% 98%;
  --secondary: 210 40% 96.1%;
  --accent: 210 40% 96.1%;
  --destructive: 0 84.2% 60.2%;       /* 警告色 红色 */
  --muted: 210 40% 96.1%;
  --muted-foreground: 215.4 16.3% 46.9%;
}
```

### 响应式断点
```css
/* Tailwind 默认断点 */
sm: 640px   /* 手机横屏 */
md: 768px   /* 平板 */
lg: 1024px  /* 小桌面 */
xl: 1280px  /* 桌面 */
2xl: 1536px /* 大桌面 */
```

### 组件规范
- 使用 shadcn/ui 组件库
- 图标使用 Lucide React
- 间距使用 4px 倍数
- 圆角统一为 8px
