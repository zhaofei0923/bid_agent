# BidAgent V2 — 前端设计文档

> 版本: 2.0.0 | 日期: 2026-02-11 | 状态: Draft

## 1. 技术选型

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 15.x | App Router + RSC + API Proxy |
| React | 18.3+ | UI 框架 |
| TypeScript | 5.6+ | 类型安全 (strict mode) |
| Tailwind CSS | 3.4+ | 原子化样式 |
| shadcn/ui | latest | 组件库 (基于 Radix UI) |
| next-intl | 4.x | 国际化 (zh/en) |
| Zustand | 5.x | 全局状态管理 |
| TanStack Query | 5.x | 服务器状态 + 缓存 |
| axios | 1.7+ | HTTP 客户端 |
| Playwright | 1.58+ | E2E 测试 |
| lucide-react | 0.460+ | 图标库 |
| date-fns | 3.6+ | 日期处理 |

---

## 2. 目录结构

```
frontend/src/
├── app/
│   ├── layout.tsx              # Root Layout: HTML + Providers
│   ├── page.tsx                # 根路由: redirect → /zh/dashboard
│   ├── providers.tsx           # QueryClientProvider
│   ├── globals.css             # Tailwind + CSS vars
│   └── [locale]/
│       ├── layout.tsx          # IntlProvider + MainLayout
│       ├── page.tsx            # 着陆页
│       ├── auth/
│       │   ├── login/page.tsx
│       │   └── register/page.tsx
│       ├── dashboard/page.tsx  # 仪表板
│       ├── opportunities/
│       │   ├── page.tsx        # 列表 + 搜索
│       │   └── [id]/page.tsx   # 详情
│       ├── projects/
│       │   ├── page.tsx        # 项目列表
│       │   └── [id]/
│       │       ├── page.tsx    # 项目详情
│       │       └── workspace/page.tsx  # 三栏投标工作台
│       ├── credits/page.tsx    # 积分管理
│       ├── settings/
│       │   ├── layout.tsx      # 设置页侧边导航
│       │   ├── profile/page.tsx
│       │   ├── credits/page.tsx
│       │   ├── notifications/page.tsx
│       │   └── security/page.tsx
│       └── help/page.tsx       # 帮助中心
│
├── components/
│   ├── ui/                     # shadcn/ui 基础组件 (V2 必须安装)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── input.tsx
│   │   ├── select.tsx
│   │   ├── badge.tsx
│   │   ├── tabs.tsx
│   │   ├── progress.tsx
│   │   ├── separator.tsx
│   │   ├── alert.tsx
│   │   ├── radio-group.tsx
│   │   ├── label.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── toast.tsx
│   │   ├── skeleton.tsx
│   │   └── tooltip.tsx
│   ├── layout/
│   │   ├── MainLayout.tsx      # AuthGuard + Header + Footer
│   │   ├── Header.tsx          # 导航 + 语言切换 + 用户菜单
│   │   └── Footer.tsx
│   ├── providers/
│   │   ├── AuthProvider.tsx    # 认证 Context (唯一)
│   │   └── ErrorBoundary.tsx   # 错误边界
│   ├── landing/                # 落地页组件
│   │   ├── LandingNav.tsx      # 顶部导航 (透明+滚动变色)
│   │   ├── HeroSection.tsx     # Hero 区域
│   │   ├── TrustBar.tsx        # 机构 Logo 条
│   │   ├── PainPointsSection.tsx   # 痛点共鸣
│   │   ├── FeaturesSection.tsx     # 功能卡片
│   │   ├── WorkflowSection.tsx     # 7 步流程
│   │   ├── ComparisonSection.tsx   # 传统 vs BidAgent
│   │   ├── PersonasSection.tsx     # 客户场景
│   │   ├── StatsSection.tsx        # 数据亮点
│   │   ├── PricingSection.tsx      # 定价方案
│   │   ├── FAQSection.tsx          # FAQ
│   │   ├── CTASection.tsx          # 底部 CTA
│   │   └── LandingFooter.tsx       # 页脚
│   ├── bid/
│   │   ├── BidProgressNav.tsx  # 左侧步骤导航
│   │   ├── BidWorkspace.tsx    # 中间内容区
│   │   ├── BidChatPanel.tsx    # 右侧 AI 聊天
│   │   ├── UploadStep.tsx      # 步骤 1: 文件上传
│   │   ├── OverviewStep.tsx    # 步骤 2: 文档概览 + AI 分析
│   │   ├── AnalysisStep.tsx    # 步骤 3: 投标分析
│   │   ├── PlanStep.tsx        # 步骤 4: 投标计划
│   │   ├── QAStep.tsx          # 步骤 5: 问答
│   │   ├── TrackingStep.tsx    # 步骤 6: 进度跟踪
│   │   ├── generation/
│   │   │   └── GenerationPanel.tsx  # AI 标书编制指导
│   │   └── quality/
│   │       └── QualityReviewPanel.tsx  # 质量审查
│   ├── opportunities/
│   │   ├── OppSearchPanel.tsx
│   │   ├── OppList.tsx
│   │   └── OppCard.tsx
│   ├── knowledge-base/
│   │   ├── BidAssistant.tsx    # 知识库聊天助手
│   │   └── DashboardAssistantWidget.tsx
│   ├── payment/
│   │   └── PaymentDialog.tsx   # 支付弹窗
│   └── settings/
│       └── SettingsLayout.tsx  # 设置页侧边导航
│
├── stores/                     # V2 新增: Zustand stores
│   ├── auth.ts                 # 认证状态
│   ├── bid-workspace.ts        # 投标工作台状态
│   └── ui.ts                   # UI 状态 (sidebar, modals)
│
├── services/                   # API 客户端 (统一 axios)
│   ├── api-client.ts           # axios 实例 + 拦截器
│   ├── auth.ts
│   ├── opportunities.ts
│   ├── projects.ts
│   ├── documents.ts
│   ├── bid-analysis.ts
│   ├── bid-plan.ts
│   ├── generation.ts
│   ├── quality-review.ts
│   ├── knowledge-base.ts
│   ├── credits.ts
│   └── stats.ts
│
├── hooks/                      # React Hooks
│   ├── use-auth.ts             # useAuth() → Zustand store
│   ├── use-opportunities.ts    # useOpportunitySearch()
│   ├── use-projects.ts         # useProjects(), useProject(id)
│   ├── use-documents.ts        # useDocuments(), useUploadDocument()
│   ├── use-bid-analysis.ts     # useBidAnalysis()
│   ├── use-generation.ts       # useGuidance(), useGuidanceStream()
│   └── use-credits.ts          # useCredits()
│
├── types/
│   ├── index.ts                # 公共类型
│   ├── auth.ts                 # User, LoginRequest, RegisterRequest
│   ├── opportunity.ts          # Opportunity, SearchParams
│   ├── project.ts              # Project, ProjectDocument
│   ├── bid.ts                  # BidStep, BidAnalysis, BidPlan
│   ├── generation.ts           # GuidanceRequest, GuidanceResponse, ReviewDraftRequest
│   └── credits.ts              # CreditTransaction, RechargePackage
│
├── lib/
│   └── utils.ts                # cn(), formatDate(), formatCurrency() 等工具
│
├── i18n/
│   ├── config.ts               # locales, defaultLocale
│   ├── request.ts              # getRequestConfig
│   └── messages/
│       ├── zh.json             # 中文翻译
│       └── en.json             # 英文翻译
│
└── middleware.ts                # next-intl locale 检测
```

---

## 3. 路由设计

### 3.1 路由表

| 路径 | 页面类型 | 认证 | 描述 |
|------|---------|------|------|
| `/` | Redirect | 否 | → `/{locale}/dashboard` |
| `/[locale]` | Server | 否 | 产品着陆页 |
| `/[locale]/auth/login` | Client | 否 | 登录 |
| `/[locale]/auth/register` | Client | 否 | 注册 |
| `/[locale]/dashboard` | Client | 是 | 仪表板：项目卡片 + AI 顾问入口 + 统计 |
| `/[locale]/opportunities` | Client | 是 | 招标机会列表 + 搜索/筛选 |
| `/[locale]/opportunities/[id]` | Client | 是 | 机会详情 + "创建项目" 按钮 |
| `/[locale]/projects` | Client | 是 | 项目列表 + 搜索/筛选 |
| `/[locale]/projects/[id]` | Client | 是 | 项目详情 + 进度概览 |
| `/[locale]/projects/[id]/workspace` | Client | 是 | **三栏投标工作台** (核心页面) |
| `/[locale]/credits` | Client | 是 | 积分余额 + 套餐购买 + 交易记录 |
| `/[locale]/settings/profile` | Client | 是 | 个人资料设置 |
| `/[locale]/settings/credits` | Client | 是 | 积分设置 |
| `/[locale]/settings/notifications` | Client | 是 | 通知偏好设置 |
| `/[locale]/settings/security` | Client | 是 | 密码 + 2FA |
| `/[locale]/help` | Client | 否 | FAQ + 使用指南 + 联系方式 |

### 3.2 Layout 层级

```
RootLayout (providers.tsx: QueryClientProvider)
└── [locale]/layout.tsx (IntlProvider + MainLayout)
    ├── page.tsx (着陆页, 无认证)
    ├── auth/* (无 MainLayout header)
    ├── dashboard (需认证)
    ├── opportunities/* (需认证)
    ├── projects/[id]/workspace (需认证, 无 Footer, 全屏)
    └── settings/layout.tsx (SettingsLayout 侧边导航)
```

### 3.3 认证路由守卫

```tsx
// components/providers/AuthProvider.tsx
export function AuthGuard({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuthStore()
  const router = useRouter()
  const pathname = usePathname()
  
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      const publicPaths = ["/", "/auth/login", "/auth/register", "/help"]
      const isPublic = publicPaths.some(p => pathname.endsWith(p))
      if (!isPublic) {
        router.replace(`/${locale}/auth/login?redirect=${pathname}`)
      }
    }
  }, [isAuthenticated, isLoading, pathname])
  
  if (isLoading) return <LoadingSkeleton />
  return <>{children}</>
}
```

---

## 4. 状态管理

### 4.1 Zustand Store 设计

#### Auth Store

```typescript
interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
}

interface AuthActions {
  login: (email: string, password: string) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
  setToken: (token: string) => void
}

export const useAuthStore = create<AuthState & AuthActions>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: true,
      
      login: async (email, password) => {
        const { access_token, user } = await authService.login({ email, password })
        set({ user, token: access_token, isAuthenticated: true })
      },
      
      logout: () => {
        set({ user: null, token: null, isAuthenticated: false })
        authService.logout()
      },
      
      refreshUser: async () => {
        try {
          const user = await authService.getCurrentUser()
          set({ user, isAuthenticated: true, isLoading: false })
        } catch {
          set({ user: null, isAuthenticated: false, isLoading: false })
        }
      },
      // ...
    }),
    { name: "auth-storage", partialize: (s) => ({ token: s.token }) }
  )
)
```

#### Bid Workspace Store

```typescript
interface BidWorkspaceState {
  projectId: string | null
  currentStep: BidStep
  completedSteps: BidStep[]
  institution: string | null
  isChatPanelOpen: boolean
}

interface BidWorkspaceActions {
  setProject: (id: string, institution: string) => void
  goToStep: (step: BidStep) => void
  completeStep: (step: BidStep) => void
  toggleChatPanel: () => void
  reset: () => void
}

export const useBidWorkspaceStore = create<BidWorkspaceState & BidWorkspaceActions>()(
  (set) => ({
    projectId: null,
    currentStep: "upload",
    completedSteps: [],
    institution: null,
    isChatPanelOpen: true,
    
    setProject: (id, institution) => set({ projectId: id, institution }),
    goToStep: (step) => set({ currentStep: step }),
    completeStep: (step) =>
      set((s) => ({
        completedSteps: s.completedSteps.includes(step)
          ? s.completedSteps
          : [...s.completedSteps, step],
      })),
    toggleChatPanel: () => set((s) => ({ isChatPanelOpen: !s.isChatPanelOpen })),
    reset: () => set({ projectId: null, currentStep: "upload", completedSteps: [] }),
  })
)
```

### 4.2 TanStack Query 模式

```typescript
// hooks/use-projects.ts
export function useProjects(params?: ProjectListParams) {
  return useQuery({
    queryKey: ["projects", params],
    queryFn: () => projectService.list(params),
    staleTime: 60_000,
  })
}

export function useProject(id: string) {
  return useQuery({
    queryKey: ["projects", id],
    queryFn: () => projectService.getById(id),
    enabled: !!id,
  })
}

export function useCreateProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: projectService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] })
    },
  })
}

// hooks/use-generation.ts
export function useGuidanceStream(projectId: string) {
  return useMutation({
    mutationFn: (message: string) => guidanceService.ask(projectId, message),
    onSuccess: (data) => {
      // 更新对话历史缓存
      queryClient.invalidateQueries({ queryKey: ["guidance-conversation", projectId] })
    },
  })
}

export function useDocumentStructure(projectId: string) {
  return useQuery({
    queryKey: ["document-structure", projectId],
    queryFn: () => guidanceService.getDocumentStructure(projectId),
    enabled: !!projectId,
  })
}
```

---

## 5. API 客户端层

### 5.1 统一 axios 实例

```typescript
// services/api-client.ts
import axios from "axios"

const apiClient = axios.create({
  baseURL: "/api/v1",
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
})

// 请求拦截: 注入 JWT
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截: 提取积分消耗、处理 401
apiClient.interceptors.response.use(
  (response) => {
    // 提取积分消耗头
    const consumed = response.headers["x-credits-consumed"]
    const remaining = response.headers["x-credits-remaining"]
    if (consumed) {
      useAuthStore.getState().updateCredits(Number(remaining))
    }
    return response
  },
  async (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
    }
    return Promise.reject(error)
  }
)

export default apiClient
```

### 5.2 Service 文件模式

```typescript
// services/projects.ts
import apiClient from "./api-client"
import type { Project, ProjectListParams, CreateProjectRequest } from "@/types/project"

export const projectService = {
  list: async (params?: ProjectListParams) => {
    const { data } = await apiClient.get<PaginatedResponse<Project>>("/projects", { params })
    return data
  },
  
  getById: async (id: string) => {
    const { data } = await apiClient.get<Project>(`/projects/${id}`)
    return data
  },
  
  create: async (req: CreateProjectRequest) => {
    const { data } = await apiClient.post<Project>("/projects", req)
    return data
  },
  
  update: async (id: string, req: Partial<Project>) => {
    const { data } = await apiClient.put<Project>(`/projects/${id}`, req)
    return data
  },
  
  delete: async (id: string) => {
    await apiClient.delete(`/projects/${id}`)
  },
}
```

---

## 6. 核心页面设计

### 6.0 产品落地页 (`/[locale]`)

> Server Component，无需认证，SEO 友好。是用户第一印象页面，需要清晰传达产品价值、建立专业信任、引导注册转化。

#### 页面结构总览

```
┌──────────────────────────────────────────────────────────┐
│  Navbar: Logo + [功能] [定价] [关于] + 语言切换 + [登录] [免费试用]  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ① Hero 区域 — 核心卖点 + CTA                             │
│                                                          │
├──────────────────────────────────────────────────────────┤
│  ② 信任条 — 合作机构 Logo (ADB / WB / UN)                  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ③ 痛点共鸣 — 传统投标难题                                  │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ④ 核心功能展示 — 四大能力卡片                               │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ⑤ 工作流可视化 — 7 步流程动态展示                           │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ⑥ 差异化优势 — 对比传统 vs BidAgent                        │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ⑦ 客户场景 — 三种角色使用案例                               │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ⑧ 数据亮点 — 关键指标动画计数                               │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ⑨ 定价方案 — 积分套餐                                     │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ⑩ FAQ — 常见问题手风琴                                    │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ⑪ 底部 CTA — 最终转化引导                                 │
│                                                          │
├──────────────────────────────────────────────────────────┤
│  Footer: 产品链接 + 法律条款 + 社交媒体 + Copyright          │
└──────────────────────────────────────────────────────────┘
```

#### ① Hero 区域

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  AI 驱动的多边机构投标助手                               │
│                                                      │
│  从招标发现到标书编制，BidAgent 用 AI 指导您高效完成       │
│  ADB · WB · UN 投标全流程，效率提升 80%                 │
│                                                      │
│  [🚀 免费试用]  [📖 了解更多]                           │
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │  产品截图 / 动画演示                           │    │
│  │  (三栏投标工作台 mockup，带毛玻璃蒙层)          │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
└──────────────────────────────────────────────────────┘
```

- **标题**: 使用 `text-5xl font-bold` 渐变色文字 (蓝→紫)
- **副标题**: `text-xl text-muted-foreground`，突出三大机构 + 效率数据
- **CTA 按钮**: Primary (免费试用 → `/auth/register`) + Secondary (了解更多 → 锚点滚动)
- **背景**: 细微的网格 pattern + 渐变 (slate-50 → blue-50)
- **产品截图**: 使用 `perspective` + `rotateX(2deg)` 营造 3D 悬浮感，配合 `shadow-2xl`

#### ② 信任条 (Trust Bar)

```
┌──────────────────────────────────────────────────────┐
│  支持的多边发展机构                                     │
│                                                      │
│  [ADB Logo]    [World Bank Logo]    [UN Logo]        │
│  亚洲开发银行     世界银行              联合国            │
└──────────────────────────────────────────────────────┘
```

- 灰度 Logo + hover 显示彩色
- `grid grid-cols-3 gap-8`，居中显示

#### ③ 痛点共鸣区

```
┌──────────────────────────────────────────────────────┐
│  传统投标，为何如此艰难？                                │
│                                                      │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐       │
│  │ ⏰          │ │ 📋         │ │ ⚠️         │       │
│  │ 耗时 2-4 周 │ │ 格式要求复杂│ │ 废标风险高  │       │
│  │ 标书编制平均 │ │ ADB/WB/UN  │ │ 30%+ 投标因│       │
│  │ 需要2-4周.. │ │ 各有不同的..│ │ 格式或内容..│       │
│  └────────────┘ └────────────┘ └────────────┘       │
│                                                      │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐       │
│  │ 🔍          │ │ 📚         │ │ 👥         │       │
│  │ 信息分散    │ │ 知识难沉淀  │ │ 团队协作断层│       │
│  │ 招标信息散布 │ │ 经验依赖资深│ │ 投标经理与..│       │
│  │ 在多个平台.. │ │ 员工，难以..│ │ 撰写人之间..│       │
│  └────────────┘ └────────────┘ └────────────┘       │
└──────────────────────────────────────────────────────┘
```

- `grid grid-cols-3 gap-6`，2 行 × 3 列布局
- 每张卡片: `Card` + `CardHeader`(icon + title) + `CardContent`(description)
- 入场动画: `Intersection Observer` + `fade-in-up`，交错 100ms

#### ④ 核心功能展示 (4 大能力)

```
┌──────────────────────────────────────────────────────┐
│  BidAgent 如何帮助您赢标？                              │
│                                                      │
│  ┌─────────────────────┐  ┌─────────────────────┐   │
│  │ 🔎 智能招标发现       │  │ 🧠 AI 深度分析       │   │
│  │                     │  │                     │   │
│  │ 自动爬取 ADB/WB/UN   │  │ 8 维度全方位解读:    │   │
│  │ 三大机构招标信息，     │  │ 资质要求、评分标准、  │   │
│  │ 智能匹配推荐，        │  │ 关键日期、BDS修改、   │   │
│  │ 不再遗漏任何机会      │  │ 风险评估...          │   │
│  │                     │  │                     │   │
│  │ [了解更多 →]         │  │ [了解更多 →]         │   │
│  └─────────────────────┘  └─────────────────────┘   │
│                                                      │
│  ┌─────────────────────┐  ┌─────────────────────┐   │
│  │ 💡 专业编制指导       │  │ ✅ 智能质量审查       │   │
│  │                     │  │                     │   │
│  │ AI 投标顾问全程指导   │  │ 4 维度自动审查:      │   │
│  │ 标书编写，提供格式    │  │ 完整性、合规性、     │   │
│  │ 要求、内容要点、      │  │ 一致性、风险识别，   │   │
│  │ 评分对标建议          │  │ 降低废标风险至 5%    │   │
│  │                     │  │                     │   │
│  │ [了解更多 →]         │  │ [了解更多 →]         │   │
│  └─────────────────────┘  └─────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

- `grid grid-cols-2 gap-8` (桌面端)，移动端 `grid-cols-1`
- 每张卡片带左侧彩色边框 (`border-l-4 border-blue-500`)
- Hover 效果: `translateY(-4px)` + `shadow-lg`
- 图标使用 `lucide-react` 对应图标，`w-10 h-10 text-primary`

#### ⑤ 工作流可视化 (7 步流程)

```
┌──────────────────────────────────────────────────────┐
│  从发现到提交，一站式投标体验                             │
│                                                      │
│  ①──────②──────③──────④──────⑤──────⑥──────⑦        │
│  发现    解析    分析    计划    编制    审查    提交     │
│  招标    文档    招标    投标    投标    质量    文件     │
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │  当前选中步骤的详细展示                         │    │
│  │  - 步骤描述                                   │    │
│  │  - 功能截图 / 动画                             │    │
│  │  - 关键特性列表 (带 ✓ 标记)                    │    │
│  └──────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────┘
```

- 水平步骤条使用 `flex items-center gap-4`，每步为可点击的圆形 + 连线
- 选中步骤高亮 (filled primary)，未选灰色
- 底部内容区: `Tab` 切换内容 + 左右布局 (文字 | 截图)
- 自动轮播: 5s 间隔，hover 暂停

**7 步内容**:

| 步骤 | 标题 | 描述 | 亮点标签 |
|------|------|------|---------|
| 1 | 发现招标 | 自动爬取 ADB/WB/UN 招标公告，全文搜索、多条件筛选 | `自动爬取` `三源聚合` |
| 2 | 文档解析 | 上传 PDF/DOCX，AI 自动解析、OCR、章节识别、向量化 | `OCR 支持` `智能分块` |
| 3 | 招标分析 | 8 维度 RAG 增强深度分析，全面理解招标要求 | `8 维度` `RAG 增强` |
| 4 | 投标计划 | AI 生成投标待办清单，从 deadline 反推时间线 | `自动规划` `甘特图` |
| 5 | 编制指导 | AI 顾问指导标书编写：格式要求、内容要点、评分对标 | `Q&A 交互` `实时指导` |
| 6 | 质量审查 | 完整性、合规性、一致性、风险 4 维度 AI 审查 | `4 维度审查` `评分预测` |
| 7 | 提交文件 | 最终检查清单 + 导出完整投标文件 | `一键导出` `合规检查` |

#### ⑥ 差异化对比 (Before / After)

```
┌──────────────────────────────────────────────────────┐
│  传统投标 vs BidAgent 智能投标                          │
│                                                      │
│  ┌───────────────────┬──────────────────────┐        │
│  │  ❌ 传统方式        │  ✅ BidAgent          │        │
│  ├───────────────────┼──────────────────────┤        │
│  │ 编制周期 2-4 周    │ 编制周期 3-5 天       │        │
│  │ 人工逐条解读招标文件│ AI 8 维度智能分析     │        │
│  │ 经验依赖个人       │ 知识库 + AI 指导      │        │
│  │ 格式错误导致废标   │ 自动合规性检查        │        │
│  │ 散落多平台找招标   │ ADB/WB/UN 三源聚合   │        │
│  │ 评分要点易遗漏     │ 评分标准自动对标      │        │
│  │ 质量全靠人工审查   │ AI 4 维度质量审查     │        │
│  └───────────────────┴──────────────────────┘        │
└──────────────────────────────────────────────────────┘
```

- 两列布局，左侧浅红背景 (`bg-red-50`)，右侧浅绿背景 (`bg-green-50`)
- 每行带 icon — ❌ / ✅
- 入场动画: 左列从左滑入，右列从右滑入

#### ⑦ 客户场景 (Personas)

```
┌──────────────────────────────────────────────────────┐
│  不同角色，都能高效投标                                  │
│                                                      │
│  [投标经理]     [技术撰写人]     [商务人员]              │
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │  👤 投标经理 — 张总监                          │    │
│  │                                              │    │
│  │  "以前评估一个 ADB 项目要花 3 天读标书，        │    │
│  │   现在 BidAgent 的 AI 分析 10 分钟就给出        │    │
│  │   Bid/No-Bid 建议，效率提升了 10 倍"           │    │
│  │                                              │    │
│  │  核心使用功能:                                 │    │
│  │  · 招标信息聚合浏览                            │    │
│  │  · AI 风险评估 + Bid/No-Bid 决策              │    │
│  │  · 投标进度跟踪                               │    │
│  └──────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────┘
```

- 3 个 Tab 切换角色场景
- 每个场景包含: 人物引言 (`blockquote`) + 核心功能列表
- 搭配角色对应的产品截图

**场景内容**:

| 角色 | 引言 | 核心功能 |
|------|------|---------|
| 投标经理 | "10 分钟完成项目可行性评估，效率提升 10 倍" | 招标浏览、风险评估、Bid/No-Bid、进度跟踪 |
| 技术撰写人 | "AI 指导让我写出评分对标的技术方案，中标率大幅提高" | 章节编写指导、评分对标、草稿审查、知识库 |
| 商务人员 | "自动解读评标方法和商务条款，报价策略更精准" | 评分标准提取、商务条款分析、预算参考 |

#### ⑧ 数据亮点 (Stats)

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│    80%↑         10min         3源          4维度      │
│   效率提升      分析耗时     招标聚合      质量审查     │
│                                                      │
│  标书编制周期    从上传到完    ADB/WB/UN    完整性/合规  │
│  从4周→5天     成8维分析     一站搜索     性/一致/风险  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

- `grid grid-cols-4 gap-8`，深色背景 (`bg-slate-900 text-white`)
- 数字使用 `text-4xl font-bold` + `CountUp` 动画 (滚入视口时触发)
- 下方描述使用 `text-sm text-slate-400`

#### ⑨ 定价方案

```
┌──────────────────────────────────────────────────────┐
│  简单透明的积分定价                                     │
│                                                      │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐       │
│  │ 体验版    │  │  ⭐ 专业版     │  │ 企业版    │       │
│  │ 免费      │  │ ¥299/月       │  │ 联系我们  │       │
│  │           │  │               │  │           │       │
│  │ 100 积分  │  │ 2,000 积分    │  │ 无限积分  │       │
│  │ 1 个项目  │  │ 不限项目      │  │ 不限项目  │       │
│  │ 基础分析  │  │ 全部分析维度  │  │ 定制功能  │       │
│  │ 社区支持  │  │ 编制指导      │  │ 专属顾问  │       │
│  │           │  │ 质量审查      │  │ API 集成  │       │
│  │           │  │ 知识库        │  │ SLA 保障  │       │
│  │           │  │ 优先支持      │  │           │       │
│  │           │  │               │  │           │       │
│  │ [开始试用] │  │ [立即订阅]    │  │ [联系销售]│       │
│  └──────────┘  └──────────────┘  └──────────┘       │
└──────────────────────────────────────────────────────┘
```

- `grid grid-cols-3 gap-6`
- 专业版卡片: `ring-2 ring-primary` 高亮 + "最受欢迎" 徽章 (`Badge`)
- 功能对比使用 `✓` / `—` 标记

#### ⑩ FAQ 手风琴

```
┌──────────────────────────────────────────────────────┐
│  常见问题                                             │
│                                                      │
│  ▸ BidAgent 支持哪些多边机构？                         │
│  ▾ AI 会直接写标书吗？                                 │
│    不会。BidAgent 的 AI 作为专业投标顾问，指导您按照      │
│    招标文件要求和规范编写标书。AI 提供格式要求、内容要      │
│    点、评分对标建议和草稿审查，但最终文档由您自行编写，     │
│    确保内容真实、准确、符合您公司的实际情况。              │
│  ▸ 数据安全如何保障？                                  │
│  ▸ 支持哪些文件格式？                                  │
│  ▸ 积分是如何消耗的？                                  │
│  ▸ 可以多人协作吗？                                    │
└──────────────────────────────────────────────────────┘
```

- 使用 shadcn/ui `Accordion` 组件
- 最大宽度 `max-w-3xl mx-auto`

**FAQ 内容**:

| 问题 | 回答要点 |
|------|---------|
| 支持哪些多边机构？ | ADB、World Bank、UN (UNGM 14 个子机构)，持续扩展中 |
| AI 会直接写标书吗？ | 不会。AI 提供指导，用户自行编写，确保内容真实准确 |
| 数据安全如何保障？ | JWT 加密认证、文件 SHA256 去重、数据库加密存储、CORS 白名单 |
| 支持哪些文件格式？ | PDF、DOCX，含扫描件 OCR 支持 |
| 积分是如何消耗的？ | 创建项目 10 积分，AI 分析按 token 计费，编制指导 20-100 积分/次 |
| 可以多人协作吗？ | V2 支持单人使用，团队协作功能在 V3 规划中 |

#### ⑪ 底部 CTA

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  准备好提升您的投标效率了吗？                             │
│                                                      │
│  免费注册，获得 100 积分体验完整功能                      │
│                                                      │
│  [🚀 立即免费开始]                                     │
│                                                      │
└──────────────────────────────────────────────────────┘
```

- 渐变背景 (`bg-gradient-to-r from-blue-600 to-purple-600`)
- 白色文字 + 白色 CTA 按钮 (`variant="outline"` 白边)
- 全宽布局，上下大留白 (`py-24`)

#### 组件拆分

```
frontend/src/components/landing/
├── LandingNav.tsx          # 顶部导航 (透明→滚动后白色)
├── HeroSection.tsx         # Hero 区域
├── TrustBar.tsx            # 机构 Logo 条
├── PainPointsSection.tsx   # 痛点共鸣
├── FeaturesSection.tsx     # 4 大功能卡片
├── WorkflowSection.tsx     # 7 步流程可视化
├── ComparisonSection.tsx   # 传统 vs BidAgent 对比
├── PersonasSection.tsx     # 客户场景 Tab
├── StatsSection.tsx        # 数据亮点 (CountUp)
├── PricingSection.tsx      # 定价方案
├── FAQSection.tsx          # FAQ 手风琴
├── CTASection.tsx          # 底部 CTA
└── LandingFooter.tsx       # 页脚
```

#### 响应式设计

| 断点 | 布局调整 |
|------|---------|
| `lg` (≥1024px) | 默认桌面布局，两列/四列网格 |
| `md` (≥768px) | 功能卡片 2 列，定价方案纵向排列 |
| `sm` (<768px) | 全部单列，Hero 文字居中，步骤条改为纵向时间线 |

#### 动画规范

| 类型 | 实现 | 触发条件 |
|------|------|---------|
| 入场淡入 | `opacity: 0→1, translateY: 20→0` | `IntersectionObserver` 进入视口 |
| 计数动画 | `CountUp` 数字滚动 (duration: 2s) | 进入视口一次 |
| 悬浮效果 | `translateY(-4px)` + `shadow-lg` | hover |
| 导航变色 | `backdrop-blur-md bg-white/80` | scroll > 50px |
| 步骤轮播 | 自动切换 active step (5s) | 自动 + 手动点击 |

#### i18n 翻译键

```json
{
  "landing": {
    "nav": {
      "features": "功能",
      "pricing": "定价",
      "about": "关于",
      "login": "登录",
      "getStarted": "免费试用"
    },
    "hero": {
      "title": "AI 驱动的多边机构投标助手",
      "subtitle": "从招标发现到标书编制，BidAgent 用 AI 指导您高效完成 ADB · WB · UN 投标全流程",
      "cta": "免费开始",
      "learnMore": "了解更多"
    },
    "trust": {
      "title": "支持的多边发展机构"
    },
    "painPoints": {
      "title": "传统投标，为何如此艰难？",
      "items": {
        "time": { "title": "耗时 2-4 周", "desc": "标书编制平均需要 2-4 周，大量时间花在理解招标文件和格式调整上" },
        "format": { "title": "格式要求复杂", "desc": "ADB/WB/UN 各有不同的招标格式规范，稍有不慎就可能废标" },
        "risk": { "title": "废标风险高", "desc": "超过 30% 的投标因格式不合规或内容遗漏而被淘汰" },
        "scattered": { "title": "信息分散", "desc": "招标信息散布在多个平台，容易遗漏优质机会" },
        "knowledge": { "title": "知识难沉淀", "desc": "经验依赖资深员工，人员流动后知识难以传承" },
        "collab": { "title": "协作断层", "desc": "投标经理与撰写人之间信息传递低效，版本管理混乱" }
      }
    },
    "features": {
      "title": "BidAgent 如何帮助您赢标？",
      "discovery": { "title": "智能招标发现", "desc": "自动爬取 ADB/WB/UN 三大机构招标信息，智能匹配推荐" },
      "analysis": { "title": "AI 深度分析", "desc": "8 维度全方位解读：资质要求、评分标准、关键日期、风险评估..." },
      "guidance": { "title": "专业编制指导", "desc": "AI 投标顾问全程指导标书编写，提供格式要求和评分对标建议" },
      "review": { "title": "智能质量审查", "desc": "4 维度自动审查：完整性、合规性、一致性、风险识别" }
    },
    "workflow": {
      "title": "从发现到提交，一站式投标体验",
      "steps": {
        "discover": "发现招标",
        "parse": "文档解析",
        "analyze": "招标分析",
        "plan": "投标计划",
        "guide": "编制指导",
        "review": "质量审查",
        "submit": "提交文件"
      }
    },
    "comparison": {
      "title": "传统投标 vs BidAgent 智能投标",
      "traditional": "传统方式",
      "bidagent": "BidAgent"
    },
    "personas": {
      "title": "不同角色，都能高效投标",
      "manager": { "name": "投标经理", "quote": "..." },
      "writer": { "name": "技术撰写人", "quote": "..." },
      "commercial": { "name": "商务人员", "quote": "..." }
    },
    "stats": {
      "efficiency": { "value": "80%", "label": "效率提升" },
      "analysisTime": { "value": "10min", "label": "分析耗时" },
      "sources": { "value": "3", "label": "招标源聚合" },
      "reviewDimensions": { "value": "4", "label": "质量审查维度" }
    },
    "pricing": {
      "title": "简单透明的积分定价",
      "free": { "name": "体验版", "price": "免费" },
      "pro": { "name": "专业版", "price": "¥299/月", "badge": "最受欢迎" },
      "enterprise": { "name": "企业版", "price": "联系我们" }
    },
    "faq": {
      "title": "常见问题"
    },
    "cta": {
      "title": "准备好提升您的投标效率了吗？",
      "subtitle": "免费注册，获得 100 积分体验完整功能",
      "button": "立即免费开始"
    }
  }
}
```

#### SEO 元数据

```tsx
// app/[locale]/page.tsx
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const t = await getTranslations("landing")
  return {
    title: "BidAgent — AI 驱动的多边机构投标助手",
    description: "从招标发现到标书编制，AI 指导您高效完成 ADB/WB/UN 投标全流程。效率提升 80%，降低废标风险。",
    keywords: ["ADB投标", "世界银行投标", "联合国采购", "标书编制", "AI投标助手"],
    openGraph: {
      title: "BidAgent — AI 驱动的多边机构投标助手",
      description: "...",
      images: ["/og-image.png"],
      type: "website",
    },
  }
}
```

---

### 6.1 投标工作台 (`/projects/[id]/workspace`)

**三栏布局** — 核心交互页面:

```
┌────────────┬───────────────────────────────┬──────────────┐
│            │                               │              │
│  Progress  │        Content Area           │   AI Chat    │
│  Nav (左)   │        (中间)                  │   Panel (右)  │
│            │                               │              │
│  7 Steps   │  根据当前步骤渲染:              │  知识库问答    │
│  ├ Upload  │  - UploadStep                 │  文档问答     │
│  ├ Interp. │  - OverviewStep               │              │
│  ├ Qualif. │  - AnalysisStep               │  双 Tab:      │
│  ├ Plan    │  - PlanStep                   │  - 知识库     │
│  ├ AIGuide │  - GenerationPanel (AI指导)       │  - 文档       │
│  ├ Review  │  - QualityReviewPanel         │              │
│  └ Track   │  - TrackingStep               │              │
│            │                               │              │
└────────────┴───────────────────────────────┴──────────────┘
     220px          flex-1 (650px+)              380px
```

**步骤流程**:

| 步骤 | 名称 | 组件 | 功能 |
|------|------|------|------|
| 1 | 文件上传 | `UploadStep` | 拖拽上传 PDF → 自动解析 → 向量化 |
| 2 | 文档解读 | `OverviewStep` | 文档结构 + AI 深度分析 + RAG 分析 + 问答 |
| 3 | 投标分析 | `AnalysisStep` | 8 步 AI 分析 (资质/评分/日期/提交/BDS/商务/方法/风险) |
| 4 | 投标计划 | `PlanStep` | AI 生成投标计划 + 任务管理 (含甘特图) |
| 5 | AI 标书 | `GenerationPanel` | Q&A 问答指导 → 章节编写指导 → 用户编写 → 草稿审查 |
| 6 | 质量审查 | `QualityReviewPanel` | 4 维度评分 + 风险标记 + 改进建议 |
| 7 | 进度跟踪 | `TrackingStep` | 任务完成度 + 即将到期 + 类别进度 |

### 6.2 机会搜索 (`/opportunities`)

```
┌───────────────────────────────────────────────┐
│  搜索面板                                      │
│  [🔍 关键词搜索] [来源▾] [国家▾] [行业▾] [日期▾] │
└───────────────────────────────────────────────┘
┌───────────────────────────────────────────────┐
│  结果列表                    排序: [最新▾]       │
│  ┌─────────────────────────────────────────┐  │
│  │ [ADB] 项目名称                  25天剩余   │  │
│  │ 国家 · 行业 · 预算范围                     │  │
│  │ [查看详情] [创建项目]                      │  │
│  └─────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────┐  │
│  │ [WB] ...                                │  │
│  └─────────────────────────────────────────┘  │
│                                               │
│  ◀ 1 2 3 ... 10 ▶                            │
└───────────────────────────────────────────────┘
```

### 6.3 仪表板 (`/dashboard`)

```
┌─────────────────────────────────────────────────┐
│  欢迎, {user.name}           积分余额: {credits} │
├────────┬────────┬────────┬──────────────────────┤
│ 进行中  │ 分析中  │ 已完成  │ 总项目数              │
│  3     │  1     │  5     │  9                   │
├────────┴────────┴────────┴──────────────────────┤
│                                                  │
│  项目列表 (最近项目)                               │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │ [ADB] 项目A │ │ [WB] 项目B  │ │ [UN] 项目C  │   │
│  │ 进度: 60%   │ │ 进度: 30%   │ │ 进度: 100%  │   │
│  │ [进入工作台] │ │ [进入工作台] │ │ [查看结果]   │   │
│  └────────────┘ └────────────┘ └────────────┘   │
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │ 🤖 AI 顾问                              │    │
│  │ 快速提问关于 ADB/WB 采购流程...            │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

---

## 7. 组件设计规范

### 7.1 组件模式

```tsx
// 标准组件模板
import { memo } from "react"
import { useTranslations } from "next-intl"

interface MyComponentProps {
  title: string
  onAction?: (id: string) => void
  isLoading?: boolean
}

export const MyComponent = memo(function MyComponent({
  title,
  onAction,
  isLoading = false,
}: MyComponentProps) {
  const t = useTranslations("myComponent")
  
  if (isLoading) return <Skeleton />
  
  return (
    <div className="rounded-lg border p-4">
      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="text-muted-foreground">{t("description")}</p>
    </div>
  )
})
```

### 7.2 文件命名

| 类型 | 命名规则 | 示例 |
|------|---------|------|
| 页面 | `page.tsx` (Next.js 约定) | `app/[locale]/dashboard/page.tsx` |
| 组件 | `PascalCase.tsx` | `BidProgressNav.tsx` |
| Hook | `use-kebab-case.ts` | `use-opportunities.ts` |
| Service | `kebab-case.ts` | `bid-analysis.ts` |
| Store | `kebab-case.ts` | `auth.ts` |
| 类型 | `kebab-case.ts` | `opportunity.ts` |
| 工具 | `kebab-case.ts` | `utils.ts` |

### 7.3 Props 规范

- 所有组件必须定义 `interface XxxProps`
- 回调函数: `on` 前缀 (`onAction`, `onStepChange`)
- 布尔值: `is`/`has` 前缀 (`isLoading`, `hasError`)
- 可选 props 使用 `?` 并提供默认值

---

## 8. 国际化方案

### 8.1 配置

```typescript
// i18n/config.ts
export const locales = ["zh", "en"] as const
export type Locale = (typeof locales)[number]
export const defaultLocale: Locale = "zh"
```

### 8.2 翻译文件结构

```json
// i18n/messages/zh.json
{
  "common": {
    "loading": "加载中...",
    "save": "保存",
    "cancel": "取消",
    "confirm": "确认",
    "delete": "删除",
    "search": "搜索",
    "noData": "暂无数据"
  },
  "nav": {
    "dashboard": "工作台",
    "opportunities": "招标机会",
    "projects": "项目管理",
    "credits": "积分",
    "settings": "设置",
    "help": "帮助"
  },
  "auth": {
    "login": "登录",
    "register": "注册",
    "email": "邮箱",
    "password": "密码",
    "logout": "退出登录"
  },
  "bid": {
    "steps": {
      "upload": "文件上传",
      "interpretation": "文档解读",
      "qualification": "投标分析",
      "plan": "投标计划",
      "aiGuide": "AI编制指导",
      "reviewCheck": "质量审查",
      "complete": "进度跟踪"
    }
  },
  "workspace": { "...": "..." },
  "opportunities": { "...": "..." },
  "dashboard": { "...": "..." },
  "credits": { "...": "..." },
  "settings": { "...": "..." },
  "help": { "...": "..." },
  "errors": {
    "generic": "出现了错误，请稍后重试",
    "network": "网络连接失败",
    "unauthorized": "请先登录",
    "notFound": "资源不存在",
    "insufficientCredits": "积分不足"
  }
}
```

### 8.3 使用规则

- **禁止硬编码中文/英文文本** — 所有 UI 文本必须通过 `useTranslations()`
- 服务端组件: `getTranslations()`
- 客户端组件: `useTranslations(namespace)`
- 动态插值: `t("greeting", { name: user.name })`
- 翻译 key 使用 `camelCase`

---

## 9. Next.js 配置

### 9.1 API 代理

```javascript
// next.config.mjs
import createNextIntlPlugin from "next-intl/plugin"

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts")

export default withNextIntl({
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/v1/:path*`,
      },
    ]
  },
})
```

### 9.2 Middleware

```typescript
// middleware.ts
import createMiddleware from "next-intl/middleware"
import { locales, defaultLocale } from "./i18n/config"

export default createMiddleware({
  locales,
  defaultLocale,
  localePrefix: "always",
})

export const config = {
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
}
```

---

## 10. TypeScript 类型定义

### 10.1 核心类型

```typescript
// types/auth.ts
interface User {
  id: string
  email: string
  name: string
  company: string | null
  avatar_url: string | null
  role: "user" | "admin"
  language: "zh" | "en"
  credits_balance: number
  created_at: string
  updated_at: string
}

interface LoginRequest {
  email: string
  password: string
}

interface RegisterRequest {
  email: string
  password: string
  name: string
  company?: string
}

interface AuthResponse {
  access_token: string
  token_type: "bearer"
  user: User
}

// types/opportunity.ts
type OpportunitySource = "adb" | "wb" | "un"
type OpportunityStatus = "open" | "closed" | "cancelled"

interface Opportunity {
  id: string
  source: OpportunitySource
  external_id: string | null
  url: string | null
  title: string
  description: string | null
  organization: string | null
  published_at: string | null
  deadline: string | null
  budget_min: number | null
  budget_max: number | null
  currency: string
  location: string | null
  country: string | null
  sector: string | null
  procurement_type: string | null
  status: OpportunityStatus
  created_at: string
}

interface SearchParams {
  search?: string
  source?: OpportunitySource
  status?: OpportunityStatus
  country?: string
  sector?: string
  sort_by?: string
  sort_order?: "asc" | "desc"
  page?: number
  page_size?: number
}

// types/project.ts
type ProjectStatus = "draft" | "analyzing" | "generating" | "review" | "submitted" | "won" | "lost"

interface Project {
  id: string
  name: string
  description: string | null
  status: ProjectStatus
  opportunity_id: string | null
  user_id: string
  progress: number
  institution: OpportunitySource | null
  current_step: string | null
  created_at: string
  updated_at: string
  opportunity?: Opportunity
}

// types/bid.ts
type BidStep = "upload" | "interpretation" | "qualification" | "plan" | "aiGuide" | "reviewCheck" | "complete"

interface BidAnalysis {
  qualification_requirements: QualificationItem[]
  evaluation_criteria: EvaluationCriteria
  key_dates: KeyDates
  submission_requirements: SubmissionRequirements
  bds_modifications: BDSModification[]
  commercial_terms: CommercialTerms
  risk_assessment: RiskAssessment
}

interface BidPlan {
  id: string
  project_id: string
  total_tasks: number
  completed_tasks: number
  tasks: BidPlanTask[]
}

interface BidPlanTask {
  id: string
  category: string
  title: string
  description: string
  status: "pending" | "in_progress" | "completed" | "cancelled"
  priority: "low" | "medium" | "high" | "critical"
  due_date: string | null
  assignee: string | null
}

// types/generation.ts — 标书编制指导相关类型

interface GuidanceRequest {
  project_id: string
  message: string
  context?: {
    section_id?: string
    intent?: "guidance" | "review" | "question"
  }
}

interface GuidanceResponse {
  message_id: string
  response: string
  route_type: "prompt" | "skill"
  skill_used?: string
  tokens_consumed: number
  credits_consumed: number
}

interface SectionGuidance {
  section_id: string
  title: string
  guidance: {
    format_requirements: string[]
    content_outline: string[]
    scoring_alignment: { criterion: string; weight: number; suggestion: string }[]
    template_references: string[]
    common_pitfalls: string[]
    word_count_target: number
  }
}

interface ReviewDraftRequest {
  project_id: string
  section_id: string
  draft_content: string
}

interface ReviewDraftResult {
  section_id: string
  overall_score: number
  format_compliance: { score: number; issues: string[] }
  content_completeness: { score: number; missing_points: string[] }
  scoring_alignment: { score: number; suggestions: string[] }
  language_quality: { score: number; improvements: string[] }
  specific_feedback: string[]
  priority_improvements: string[]
}

interface DocumentStructure {
  project_id: string
  title: string
  sections: DocumentSection[]
}

interface DocumentSection {
  id: string
  title: string
  requirements: string
  scoring_weight: number
  format_requirements: string[]
  status: "not_started" | "drafting" | "reviewed" | "completed"
}
}

interface OutlineSection {
  id: string
  title: string
  word_count_target: number
  subsections?: string[]
  key_points?: string[]
  linked_criteria?: string[]
}

interface SectionContent {
  section_id: string
  title: string
  content: string
  word_count: number
  quality_score?: number
}
```

### 10.2 通用类型

```typescript
// types/index.ts
interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

interface ApiError {
  code: string
  message: string
  details?: Record<string, string[]>
}
```

---

## 11. SSE 流式输出

### 11.1 标书编制指导流式

```typescript
// services/generation.ts
export async function* streamGuidance(
  projectId: string,
  message: string,
): AsyncGenerator<GuidanceEvent> {
  const token = useAuthStore.getState().token
  const response = await fetch(`/api/v1/guidance/ask-stream`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "text/event-stream",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ project_id: projectId, message }),
  })
  
  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split("\n\n")
    buffer = lines.pop()!
    
    for (const chunk of lines) {
      if (chunk.startsWith("data: ")) {
        const data = JSON.parse(chunk.slice(6))
        yield data as GuidanceEvent
      }
    }
  }
}

// 事件类型
type GuidanceEvent =
  | { type: "thinking"; message: string }
  | { type: "chunk"; content: string }
  | { type: "reference"; source: string; content: string }
  | { type: "complete"; message_id: string; route_type: string; tokens_consumed: number }
  | { type: "error"; message: string; code: string }
```

### 11.2 使用示例

```tsx
// components/bid/generation/GenerationPanel.tsx
function useStreamGuidance(projectId: string) {
  const [response, setResponse] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)
  
  const sendMessage = useCallback(async (message: string) => {
    setIsStreaming(true)
    setResponse("")
    
    for await (const event of streamGuidance(projectId, message)) {
      switch (event.type) {
        case "thinking":
          // 显示思考状态
          break
        case "chunk":
          setResponse(prev => prev + event.content)
          break
        case "reference":
          // 显示引用来源
          break
        case "complete":
          setIsStreaming(false)
          queryClient.invalidateQueries({ queryKey: ["guidance-conversation", projectId] })
          break
      }
    }
  }, [projectId])
  
  return { response, isStreaming, sendMessage }
}
```

---

## 12. 错误处理

### 12.1 ErrorBoundary

```tsx
// components/providers/ErrorBoundary.tsx
export class ErrorBoundary extends React.Component<Props, State> {
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }
  
  render() {
    if (this.state.hasError) {
      return this.props.fallback || <DefaultErrorUI error={this.state.error} />
    }
    return this.props.children
  }
}

// 预设变体
export const PageErrorBoundary = ({ children }) => (
  <ErrorBoundary fallback={<FullPageError />}>{children}</ErrorBoundary>
)

export const SectionErrorBoundary = ({ children }) => (
  <ErrorBoundary fallback={<SectionError />}>{children}</ErrorBoundary>
)
```

### 12.2 API 错误处理

```typescript
// hooks 中统一处理
const { data, error, isError } = useQuery(...)

if (isError) {
  if (error.response?.status === 402) {
    // 积分不足 → 打开支付弹窗
    openPaymentDialog()
  }
  // toast 提示
  toast.error(t(`errors.${error.response?.data?.code || "generic"}`))
}
```

---

## 13. V1 → V2 改进

| 方面 | V1 问题 | V2 方案 |
|------|--------|---------|
| 组件库 | shadcn/ui 引用未安装 | 完整安装 shadcn/ui |
| 状态管理 | Context + useState 散乱 | Zustand (全局) + TanStack Query (服务器) |
| 认证 | useAuth hook + AuthProvider 重复 | 统一 Zustand authStore |
| API 客户端 | axios + fetch 混用 | 统一 axios + 拦截器 |
| Mock 数据 | 多页面硬编码 mock | 全部真实 API |
| 工作流步骤 | 7 步 + 8 步两套命名 | 统一 7 步 BidStep |
| 类型安全 | 集中单文件 index.ts | 按域拆分 types/ |
| 错误处理 | 基础 try/catch | ErrorBoundary + toast + 积分不足弹窗 |
| SSE | 伪 SSE | 标准 text/event-stream |
