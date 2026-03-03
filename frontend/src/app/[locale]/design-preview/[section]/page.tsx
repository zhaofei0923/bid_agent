import { notFound } from "next/navigation"
import { getTranslations } from "next-intl/server"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { PreviewSection } from "@/components/design-preview/PreviewSection"

const ALLOWED_SECTIONS = [
  "overview",
  "auth",
  "dashboard",
  "search",
  "opportunities",
  "projects",
  "workspace",
  "credits",
  "help",
  "settings",
  "states",
] as const

type SectionKey = (typeof ALLOWED_SECTIONS)[number]

function RouteHero({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string
  title: string
  description: string
}) {
  return (
    <section className="app-section-frame px-6 py-8 sm:px-8 sm:py-10">
      <p className="app-page-kicker">{eyebrow}</p>
      <h1 className="app-page-title mt-4">{title}</h1>
      <p className="app-page-subtitle mt-4 max-w-3xl">{description}</p>
    </section>
  )
}

function StatPreviewCard({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div className="app-surface app-stat-card px-6 py-6">
      <p className="text-sm font-medium text-stone-500">{label}</p>
      <p className="app-metric-value mt-4">{value}</p>
    </div>
  )
}

function PreviewOpportunityCard({
  source,
  status,
  title,
  description,
  meta,
}: {
  source: string
  status: string
  title: string
  description: string
  meta: string
}) {
  return (
    <div className="app-surface px-5 py-5">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="secondary">{source}</Badge>
        <Badge variant="outline">{status}</Badge>
      </div>
      <p className="mt-4 text-lg font-semibold tracking-[-0.02em] text-slate-900">
        {title}
      </p>
      <p className="mt-2 text-sm leading-7 text-stone-600">{description}</p>
      <p className="mt-4 text-xs font-semibold uppercase tracking-[0.12em] text-stone-400">
        {meta}
      </p>
    </div>
  )
}

function PreviewProjectCard({
  title,
  status,
  progress,
  step,
  subtitle,
}: {
  title: string
  status: string
  progress: number
  step: string
  subtitle: string
}) {
  return (
    <div className="app-surface px-5 py-5">
      <div className="flex items-start justify-between gap-3">
        <p className="text-lg font-semibold tracking-[-0.02em] text-slate-900">
          {title}
        </p>
        <Badge variant="secondary">{status}</Badge>
      </div>
      <p className="mt-2 text-sm leading-7 text-stone-600">{subtitle}</p>
      <div className="mt-5 flex items-center justify-between text-sm text-stone-500">
        <span>{step}</span>
        <span>{progress}%</span>
      </div>
      <div className="app-progress-track mt-3">
        <div className="app-progress-fill" style={{ width: `${progress}%` }} />
      </div>
    </div>
  )
}

function DetailTile({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div className="app-surface-muted px-4 py-4">
      <p className="app-detail-label">{label}</p>
      <p className="app-detail-value mt-2">{value}</p>
    </div>
  )
}

export default async function DesignPreviewSectionPage({
  params,
}: {
  params: Promise<{ locale: string; section: string }>
}) {
  const { locale, section } = await params

  if (!ALLOWED_SECTIONS.includes(section as SectionKey)) {
    notFound()
  }

  const tCommon = await getTranslations({ locale, namespace: "common" })
  const tAuth = await getTranslations({ locale, namespace: "auth" })
  const tDashboard = await getTranslations({ locale, namespace: "dashboard" })
  const tSearch = await getTranslations({ locale, namespace: "publicSearch" })
  const tOpportunities = await getTranslations({
    locale,
    namespace: "opportunities",
  })
  const tProjects = await getTranslations({ locale, namespace: "projects" })
  const tWorkspace = await getTranslations({ locale, namespace: "workspace" })
  const tCredits = await getTranslations({ locale, namespace: "credits" })
  const tHelp = await getTranslations({ locale, namespace: "help" })
  const tSettings = await getTranslations({ locale, namespace: "settings" })
  const tLanding = await getTranslations({ locale, namespace: "landingV2" })

  const trustNotes = tLanding.raw("hero.trustNotes") as string[]
  const plans = tLanding.raw("pricing.plans") as Array<{
    name: string
    summary: string
    price: string
    period: string
  }>
  const guideItems = tHelp.raw("guideItems") as Array<{ title: string; desc: string }>
  const faqItems = tHelp.raw("faqItems") as Array<{ q: string; a: string }>

  const dashboardStats = [
    { label: tDashboard("activeProjects"), value: "12" },
    { label: tDashboard("totalOpportunities"), value: "48" },
    { label: tDashboard("creditsBalance"), value: "680" },
  ]

  const dashboardActions = [
    {
      title: tDashboard("browseOpportunities"),
      description: tDashboard("browseOpportunitiesDesc"),
    },
    {
      title: tDashboard("startBidProject"),
      description: tDashboard("createProject"),
    },
  ]

  const previewOpportunities = [
    {
      source: "ADB",
      status: tOpportunities("statusOpen"),
      title: "Nepal Urban Water Systems Advisory",
      description: tOpportunities("noResultsHint"),
      meta: "Nepal  |  Water  |  2026-06-30",
    },
    {
      source: "WB",
      status: tOpportunities("statusOpen"),
      title: "Regional Climate Resilience TA",
      description: tSearch("subtitle"),
      meta: "Vietnam  |  Advisory  |  USD 120,000",
    },
    {
      source: "UN",
      status: tOpportunities("statusOpen"),
      title: "Digital Procurement Modernization",
      description: tDashboard("browseOpportunitiesDesc"),
      meta: "Hybrid  |  Governance  |  8 days left",
    },
  ]

  const previewProjects = [
    {
      title: "WB Corridor Mobility Bid",
      status: tCommon("active"),
      progress: 72,
      step: tWorkspace("steps.analysis"),
      subtitle: tProjects("createdOn", { date: "2026-02-24" }),
    },
    {
      title: "ADB Smart Grid Proposal",
      status: tCommon("active"),
      progress: 58,
      step: tWorkspace("steps.plan"),
      subtitle: tProjects("createdOn", { date: "2026-02-18" }),
    },
    {
      title: "UN Health Logistics Pilot",
      status: tCommon("active"),
      progress: 34,
      step: tWorkspace("steps.upload"),
      subtitle: tProjects("createdOn", { date: "2026-02-10" }),
    },
  ]

  const projectDetailTiles = [
    { label: tProjects("status"), value: tCommon("active") },
    { label: tProjects("progress"), value: "72%" },
    { label: tProjects("currentStep"), value: tWorkspace("steps.analysis") },
  ]

  const authSection = (
    <PreviewSection eyebrow={tAuth("loginButton")} title={tAuth("loginTitle")}>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="app-surface px-6 py-6">
          <label className="mb-2 block text-sm font-medium text-stone-700">
            {tAuth("email")}
          </label>
          <Input value="team@bidagent.ai" readOnly />
          <label className="mb-2 mt-4 block text-sm font-medium text-stone-700">
            {tAuth("password")}
          </label>
          <Input type="password" value="password" readOnly />
          <Button className="mt-5 w-full">{tAuth("loginButton")}</Button>
        </div>
        <div className="app-surface px-6 py-6">
          <label className="mb-2 block text-sm font-medium text-stone-700">
            {tAuth("name")}
          </label>
          <Input value="BidAgent Team" readOnly />
          <label className="mb-2 mt-4 block text-sm font-medium text-stone-700">
            {tAuth("company")}
          </label>
          <Input value="Easu Data" readOnly />
          <Button className="mt-5 w-full">{tAuth("registerButton")}</Button>
        </div>
      </div>
    </PreviewSection>
  )

  const dashboardSection = (
    <PreviewSection eyebrow={tDashboard("title")} title={tDashboard("title")}>
      <div className="space-y-6">
        <div className="grid gap-4 lg:grid-cols-3">
          {dashboardStats.map((item) => (
            <StatPreviewCard
              key={item.label}
              label={item.label}
              value={item.value}
            />
          ))}
        </div>

        <div className="app-section-frame px-6 py-6">
          <p className="app-page-kicker">{tDashboard("quickStart")}</p>
          <h3 className="app-section-title mt-3">{tDashboard("quickStart")}</h3>
          <div className="mt-5 grid gap-4 lg:grid-cols-2">
            {dashboardActions.map((item) => (
              <div key={item.title} className="app-surface px-5 py-5">
                <p className="text-lg font-semibold tracking-[-0.02em] text-slate-900">
                  {item.title}
                </p>
                <p className="mt-2 text-sm leading-7 text-stone-600">
                  {item.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="grid gap-4 xl:grid-cols-[1.18fr_0.82fr]">
          <div className="app-section-frame px-6 py-6">
            <p className="app-page-kicker">{tDashboard("latestOpportunities")}</p>
            <h3 className="app-section-title mt-3">
              {tDashboard("latestOpportunities")}
            </h3>
            <div className="mt-5 space-y-4">
              {previewOpportunities.map((item) => (
                <PreviewOpportunityCard
                  key={item.title}
                  source={item.source}
                  status={item.status}
                  title={item.title}
                  description={item.description}
                  meta={item.meta}
                />
              ))}
            </div>
          </div>

          <div className="app-section-frame px-6 py-6">
            <p className="app-page-kicker">{tDashboard("recentProjects")}</p>
            <h3 className="app-section-title mt-3">
              {tDashboard("recentProjects")}
            </h3>
            <div className="mt-5 space-y-4">
              {previewProjects.slice(0, 2).map((item) => (
                <PreviewProjectCard
                  key={item.title}
                  title={item.title}
                  status={item.status}
                  progress={item.progress}
                  step={item.step}
                  subtitle={item.subtitle}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </PreviewSection>
  )

  const searchSection = (
    <PreviewSection eyebrow={tSearch("title")} title={tSearch("title")}>
      <div className="space-y-4">
        <div className="app-surface px-6 py-6">
          <Input value={tOpportunities("search")} readOnly />
        </div>
        <div className="grid gap-4">
          {previewOpportunities.slice(0, 2).map((item) => (
            <PreviewOpportunityCard
              key={item.title}
              source={item.source}
              status={item.status}
              title={item.title}
              description={item.description}
              meta={item.meta}
            />
          ))}
        </div>
      </div>
    </PreviewSection>
  )

  const opportunitiesSection = (
    <PreviewSection
      eyebrow={tOpportunities("title")}
      title={tOpportunities("viewDetail")}
    >
      <div className="grid gap-4 xl:grid-cols-[1.08fr_0.92fr]">
        <div className="app-section-frame px-6 py-6">
          <Input value={tOpportunities("search")} readOnly />
          <div className="mt-5 space-y-4">
            {previewOpportunities.slice(0, 2).map((item) => (
              <PreviewOpportunityCard
                key={item.title}
                source={item.source}
                status={item.status}
                title={item.title}
                description={item.description}
                meta={item.meta}
              />
            ))}
          </div>
        </div>
        <div className="app-section-frame px-6 py-6">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">WB</Badge>
            <Badge variant="outline">{tOpportunities("statusOpen")}</Badge>
          </div>
          <p className="mt-4 text-xl font-semibold tracking-[-0.02em] text-slate-900">
            Regional Climate Resilience TA
          </p>
          <p className="mt-2 text-sm leading-7 text-stone-600">
            {tOpportunities("noResultsHint")}
          </p>
          <div className="mt-6 grid gap-3">
            <DetailTile label={tOpportunities("deadline")} value="2026-06-30" />
            <DetailTile label={tOpportunities("budget")} value="$120,000" />
            <DetailTile label={tOpportunities("country")} value="Vietnam" />
            <DetailTile label={tOpportunities("organization")} value="World Bank" />
          </div>
        </div>
      </div>
    </PreviewSection>
  )

  const projectsSection = (
    <PreviewSection eyebrow={tProjects("title")} title={tProjects("openWorkspace")}>
      <div className="grid gap-4 xl:grid-cols-[1.14fr_0.86fr]">
        <div className="app-section-frame px-6 py-6">
          <p className="app-page-kicker">{tProjects("title")}</p>
          <h3 className="app-section-title mt-3">{tProjects("title")}</h3>
          <div className="mt-5 space-y-4">
            {previewProjects.map((item) => (
              <PreviewProjectCard
                key={item.title}
                title={item.title}
                status={item.status}
                progress={item.progress}
                step={item.step}
                subtitle={item.subtitle}
              />
            ))}
          </div>
        </div>

        <div className="app-section-frame px-6 py-6">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">{tCommon("active")}</Badge>
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-stone-400">
              WB-2026-004
            </span>
          </div>

          <p className="mt-4 text-2xl font-semibold tracking-[-0.03em] text-slate-900">
            {previewProjects[0]?.title}
          </p>
          <p className="mt-2 text-sm leading-7 text-stone-600">
            {previewProjects[0]?.subtitle}
          </p>

          <div className="mt-6 grid gap-3">
            {projectDetailTiles.map((item) => (
              <DetailTile
                key={item.label}
                label={item.label}
                value={item.value}
              />
            ))}
          </div>

          <div className="mt-6">
            <div className="flex items-center justify-between text-sm text-stone-500">
              <span>{tProjects("progress")}</span>
              <span>72%</span>
            </div>
            <div className="app-progress-track mt-3">
              <div className="app-progress-fill" style={{ width: "72%" }} />
            </div>
          </div>

          <div className="app-surface-muted mt-6 px-4 py-4">
            <p className="app-detail-label">{tProjects("currentStep")}</p>
            <p className="mt-2 text-sm leading-7 text-stone-600">
              {tWorkspace("steps.analysis")} · {tProjects("openWorkspace")}
            </p>
          </div>
        </div>
      </div>
    </PreviewSection>
  )

  const workspaceSection = (
    <PreviewSection eyebrow={tWorkspace("title")} title={tWorkspace("stepsTitle")}>
      <div className="grid gap-4 xl:grid-cols-[0.28fr_0.42fr_0.3fr]">
        <div className="app-surface px-5 py-5">
          <div className="space-y-2">
            {[
              tWorkspace("steps.upload"),
              tWorkspace("steps.analysis"),
              tWorkspace("steps.plan"),
              tWorkspace("steps.review"),
            ].map((step, index) => (
              <div
                key={step}
                className={`rounded-2xl px-4 py-3 text-sm font-medium ${
                  index === 1 ? "bg-slate-900 text-white" : "bg-stone-100 text-stone-700"
                }`}
              >
                {step}
              </div>
            ))}
          </div>
        </div>
        <div className="app-surface px-6 py-6">
          <p className="text-lg font-semibold text-slate-900">
            {tWorkspace("steps.analysis")}
          </p>
          <Textarea className="mt-4" value={tWorkspace("chat.greetingHint")} readOnly />
        </div>
        <div className="app-surface px-5 py-5">
          <p className="text-sm font-semibold text-slate-900">
            {tWorkspace("chat.title")}
          </p>
          <div className="mt-4 rounded-2xl bg-stone-100 px-4 py-3 text-sm leading-7 text-stone-700">
            {tWorkspace("chat.greeting")}
          </div>
          <Input className="mt-4" value={tWorkspace("chat.placeholder")} readOnly />
        </div>
      </div>
    </PreviewSection>
  )

  const creditsSection = (
    <PreviewSection eyebrow={tCredits("title")} title={tCredits("packages")}>
      <div className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="app-section-frame px-6 py-6">
          <p className="app-page-kicker">{tCredits("balance")}</p>
          <p className="app-metric-value mt-4">680</p>
          <p className="mt-2 text-sm text-stone-600">{tCredits("creditsUnit")}</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {plans.slice(0, 2).map((plan) => (
            <div key={plan.name} className="app-surface px-6 py-6">
              <p className="text-lg font-semibold text-slate-900">{plan.name}</p>
              <p className="mt-2 text-sm leading-7 text-stone-600">{plan.summary}</p>
              <p className="mt-4 text-base font-semibold text-stone-700">
                {plan.price}
                {plan.period ? ` / ${plan.period}` : ""}
              </p>
            </div>
          ))}
        </div>
      </div>
    </PreviewSection>
  )

  const helpSection = (
    <PreviewSection eyebrow={tHelp("title")} title={tHelp("faq")}>
      <div className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="app-surface px-6 py-6">
          <Input value={tHelp("searchPlaceholder")} readOnly />
          <div className="mt-5 space-y-3">
            {guideItems.slice(0, 2).map((item) => (
              <div key={item.title} className="app-surface-muted px-4 py-4">
                <p className="font-medium text-slate-900">{item.title}</p>
                <p className="mt-1 text-sm leading-7 text-stone-600">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="space-y-3">
          {faqItems.slice(0, 2).map((item) => (
            <div key={item.q} className="app-surface px-5 py-5">
              <p className="font-medium text-slate-900">{item.q}</p>
              <p className="mt-2 text-sm leading-7 text-stone-600">{item.a}</p>
            </div>
          ))}
        </div>
      </div>
    </PreviewSection>
  )

  const settingsSection = (
    <PreviewSection eyebrow={tSettings("title")} title={tSettings("profilePage.title")}>
      <div className="grid gap-4 xl:grid-cols-[0.3fr_0.7fr]">
        <div className="app-surface px-4 py-4">
          {[tSettings("profile"), tSettings("credits"), tSettings("notifications"), tSettings("security")].map(
            (item, index) => (
              <div
                key={item}
                className={`rounded-2xl px-4 py-3 text-sm font-medium ${
                  index === 0 ? "bg-slate-900 text-white" : "text-stone-600"
                }`}
              >
                {item}
              </div>
            )
          )}
        </div>
        <div className="app-surface px-6 py-6">
          <label className="mb-2 block text-sm font-medium text-stone-700">
            {tSettings("profilePage.email")}
          </label>
          <Input value="team@bidagent.ai" readOnly />
          <label className="mb-2 mt-4 block text-sm font-medium text-stone-700">
            {tSettings("profilePage.name")}
          </label>
          <Input value="BidAgent Team" readOnly />
          <Button className="mt-5">{tCommon("save")}</Button>
        </div>
      </div>
    </PreviewSection>
  )

  const statesSection = (
    <PreviewSection eyebrow={tCommon("error")} title={tCommon("noData")}>
      <div className="grid gap-4 md:grid-cols-3">
        {[tCommon("loading"), tCommon("noData"), tCommon("error")].map((item) => (
          <div key={item} className="app-empty-state px-6 py-10 text-center">
            <p className="font-semibold text-slate-900">{item}</p>
            <p className="mt-2 text-sm leading-7 text-stone-600">{tCommon("retry")}</p>
          </div>
        ))}
      </div>
    </PreviewSection>
  )

  if (section === "overview") {
    return (
      <>
        <section className="app-section-frame px-6 py-8 sm:px-8 sm:py-10">
          <p className="app-page-kicker">{tCommon("appName")}</p>
          <h1 className="app-page-title mt-4">{tLanding("metaTitle")}</h1>
          <p className="app-page-subtitle mt-4 max-w-3xl">
            {tLanding("metaDescription")}
          </p>
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {trustNotes.map((note) => (
              <div key={note} className="app-surface-muted px-4 py-4">
                <p className="text-sm font-medium leading-7 text-stone-700">{note}</p>
              </div>
            ))}
          </div>
        </section>
        {authSection}
        {dashboardSection}
        {searchSection}
        {opportunitiesSection}
        {projectsSection}
        {workspaceSection}
        {creditsSection}
        {helpSection}
        {settingsSection}
        {statesSection}
      </>
    )
  }

  if (section === "auth") {
    return (
      <>
        <RouteHero
          eyebrow="Auth"
          title="Authentication Preview"
          description="独立捕获登录与注册页面的预览板。"
        />
        {authSection}
      </>
    )
  }

  if (section === "dashboard") {
    return (
      <>
        <RouteHero
          eyebrow={tDashboard("title")}
          title="Dashboard Preview"
          description="独立捕获仪表板卡片、快速入口和最近项目板块。"
        />
        {dashboardSection}
      </>
    )
  }

  if (section === "search") {
    return (
      <>
        <RouteHero
          eyebrow={tSearch("title")}
          title="Search Preview"
          description="独立捕获搜索框、筛选条和结果列表。"
        />
        {searchSection}
      </>
    )
  }

  if (section === "opportunities") {
    return (
      <>
        <RouteHero
          eyebrow={tOpportunities("title")}
          title="Opportunities Preview"
          description="独立捕获商机列表与详情信息结构。"
        />
        {opportunitiesSection}
      </>
    )
  }

  if (section === "projects") {
    return (
      <>
        <RouteHero
          eyebrow={tProjects("title")}
          title="Projects Preview"
          description="独立捕获项目列表、状态信息和进度详情板块。"
        />
        {projectsSection}
      </>
    )
  }

  if (section === "workspace") {
    return (
      <>
        <RouteHero
          eyebrow={tWorkspace("title")}
          title="Workspace Preview"
          description="独立捕获工作台的三栏结构和 AI 侧栏。"
        />
        {workspaceSection}
      </>
    )
  }

  if (section === "credits") {
    return (
      <>
        <RouteHero
          eyebrow={tCredits("title")}
          title="Credits Preview"
          description="独立捕获积分余额、套餐和支付入口。"
        />
        {creditsSection}
      </>
    )
  }

  if (section === "help") {
    return (
      <>
        <RouteHero
          eyebrow={tHelp("title")}
          title="Help Preview"
          description="独立捕获帮助中心与 FAQ 结构。"
        />
        {helpSection}
      </>
    )
  }

  if (section === "settings") {
    return (
      <>
        <RouteHero
          eyebrow={tSettings("title")}
          title="Settings Preview"
          description="独立捕获设置导航与账户表单。"
        />
        {settingsSection}
      </>
    )
  }

  return (
    <>
      <RouteHero
        eyebrow={tCommon("error")}
        title="Shared States Preview"
        description="独立捕获加载、空状态与错误提示。"
      />
      {statesSection}
    </>
  )
}
