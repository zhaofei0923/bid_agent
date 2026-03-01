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
    <section className="app-panel px-6 py-8 sm:px-8 sm:py-10">
      <p className="app-page-kicker">{eyebrow}</p>
      <h1 className="app-page-title mt-4">{title}</h1>
      <p className="app-page-subtitle mt-4 max-w-3xl">{description}</p>
    </section>
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
  const tOpportunities = await getTranslations({ locale, namespace: "opportunities" })
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

  const authSection = (
    <PreviewSection eyebrow={tAuth("loginButton")} title={tAuth("loginTitle")}>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="app-surface px-6 py-6">
          <label className="mb-2 block text-sm font-medium text-stone-700">{tAuth("email")}</label>
          <Input value="team@bidagent.ai" readOnly />
          <label className="mb-2 mt-4 block text-sm font-medium text-stone-700">{tAuth("password")}</label>
          <Input type="password" value="password" readOnly />
          <Button className="mt-5 w-full">{tAuth("loginButton")}</Button>
        </div>
        <div className="app-surface px-6 py-6">
          <label className="mb-2 block text-sm font-medium text-stone-700">{tAuth("name")}</label>
          <Input value="BidAgent Team" readOnly />
          <label className="mb-2 mt-4 block text-sm font-medium text-stone-700">{tAuth("company")}</label>
          <Input value="Easu Data" readOnly />
          <Button className="mt-5 w-full">{tAuth("registerButton")}</Button>
        </div>
      </div>
    </PreviewSection>
  )

  const dashboardSection = (
    <PreviewSection eyebrow={tDashboard("title")} title={tDashboard("title")}>
      <div className="grid gap-4 lg:grid-cols-3">
        {[tDashboard("activeProjects"), tDashboard("totalOpportunities"), tDashboard("creditsBalance")].map((item, index) => (
          <div key={item} className="app-surface px-6 py-6">
            <p className="text-sm text-stone-500">{item}</p>
            <p className="landing-v2-display mt-4 text-4xl font-semibold text-slate-900">
              {index === 0 ? "12" : index === 1 ? "48" : "680"}
            </p>
          </div>
        ))}
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
          {Array.from({ length: 2 }).map((_, index) => (
            <div key={index} className="app-surface px-6 py-6">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="secondary">ADB</Badge>
                <Badge variant="outline">{tOpportunities("statusOpen")}</Badge>
              </div>
              <p className="mt-3 text-xl font-semibold text-slate-900">{tOpportunities("title")}</p>
              <p className="mt-2 text-sm leading-7 text-stone-600">{tSearch("subtitle")}</p>
            </div>
          ))}
        </div>
      </div>
    </PreviewSection>
  )

  const opportunitiesSection = (
    <PreviewSection eyebrow={tOpportunities("title")} title={tOpportunities("viewDetail")}>
      <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="app-surface px-6 py-6">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">WB</Badge>
            <Badge variant="outline">{tOpportunities("statusOpen")}</Badge>
          </div>
          <p className="mt-4 text-xl font-semibold text-slate-900">{tOpportunities("title")}</p>
          <p className="mt-2 text-sm leading-7 text-stone-600">{tOpportunities("noResultsHint")}</p>
        </div>
        <div className="app-surface px-6 py-6">
          <p className="app-inline-label">{tOpportunities("deadline")}</p>
          <p className="mt-2 text-lg font-semibold text-slate-900">2026-06-30</p>
          <p className="app-inline-label mt-6">{tOpportunities("budget")}</p>
          <p className="mt-2 text-lg font-semibold text-slate-900">$120,000</p>
        </div>
      </div>
    </PreviewSection>
  )

  const projectsSection = (
    <PreviewSection eyebrow={tProjects("title")} title={tProjects("openWorkspace")}>
      <div className="grid gap-4 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <div key={index} className="app-surface px-6 py-6">
            <div className="flex items-center justify-between gap-3">
              <p className="text-lg font-semibold text-slate-900">{tProjects("title")}</p>
              <Badge variant="secondary">{tCommon("active")}</Badge>
            </div>
            <p className="mt-2 text-sm leading-7 text-stone-600">{tProjects("description")}</p>
            <div className="mt-5 h-2.5 rounded-full bg-stone-100">
              <div className="h-2.5 rounded-full bg-slate-900" style={{ width: `${65 + index * 10}%` }} />
            </div>
          </div>
        ))}
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
          <p className="text-lg font-semibold text-slate-900">{tWorkspace("steps.analysis")}</p>
          <Textarea
            className="mt-4"
            value={tWorkspace("chat.greetingHint")}
            readOnly
          />
        </div>
        <div className="app-surface px-5 py-5">
          <p className="text-sm font-semibold text-slate-900">{tWorkspace("chat.title")}</p>
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
        <div className="app-panel px-6 py-6">
          <p className="app-page-kicker">{tCredits("balance")}</p>
          <p className="landing-v2-display mt-4 text-5xl font-semibold text-slate-900">680</p>
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
          {[tSettings("profile"), tSettings("credits"), tSettings("notifications"), tSettings("security")].map((item, index) => (
            <div
              key={item}
              className={`rounded-2xl px-4 py-3 text-sm font-medium ${
                index === 0 ? "bg-slate-900 text-white" : "text-stone-600"
              }`}
            >
              {item}
            </div>
          ))}
        </div>
        <div className="app-surface px-6 py-6">
          <label className="mb-2 block text-sm font-medium text-stone-700">{tSettings("profilePage.email")}</label>
          <Input value="team@bidagent.ai" readOnly />
          <label className="mb-2 mt-4 block text-sm font-medium text-stone-700">{tSettings("profilePage.name")}</label>
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
        <section className="app-panel px-6 py-8 sm:px-8 sm:py-10">
          <p className="app-page-kicker">{tCommon("appName")}</p>
          <h1 className="app-page-title mt-4">{tLanding("metaTitle")}</h1>
          <p className="app-page-subtitle mt-4 max-w-3xl">{tLanding("metaDescription")}</p>
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
          description="独立捕获仪表板卡片与欢迎区。"
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
          description="独立捕获项目列表、状态与进度卡片。"
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
