import Link from "next/link"
import { getTranslations } from "next-intl/server"
import { ArrowUpRight } from "lucide-react"

const PREVIEW_SECTIONS = [
  { key: "overview", title: "Overview", desc: "全站风格总览，适合一次性输出系统板。"},
  { key: "auth", title: "Auth", desc: "登录与注册表单预览。"},
  { key: "dashboard", title: "Dashboard", desc: "仪表板与概览卡片。"},
  { key: "search", title: "Search", desc: "公开搜索与结果列表。"},
  { key: "opportunities", title: "Opportunities", desc: "商机列表与详情展示。"},
  { key: "projects", title: "Projects", desc: "项目列表与项目详情。"},
  { key: "workspace", title: "Workspace", desc: "工作台三栏结构与 AI 侧栏。"},
  { key: "credits", title: "Credits", desc: "积分余额、套餐与交易记录。"},
  { key: "help", title: "Help", desc: "帮助中心与 FAQ。"},
  { key: "settings", title: "Settings", desc: "设置导航与账户表单。"},
  { key: "states", title: "Shared States", desc: "加载、空状态与错误提示。"},
] as const

export default async function DesignPreviewIndexPage({
  params,
}: {
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params
  const tCommon = await getTranslations({ locale, namespace: "common" })

  return (
    <>
      <section className="app-panel px-6 py-8 sm:px-8 sm:py-10">
        <p className="app-page-kicker">Design Preview</p>
        <h1 className="app-page-title mt-4">BidAgent Product UI Capture Routes</h1>
        <p className="app-page-subtitle mt-4 max-w-3xl">
          独立预览路由已经拆分完成。你可以逐个打开下面的页面，用 Figma MCP
          单独捕获每类页面，也可以先用 overview 产出总览稿。
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href={`/${locale}`}
            className="inline-flex h-11 items-center rounded-full border border-stone-300 bg-white px-5 text-sm font-semibold text-stone-700 transition-colors duration-200 hover:text-slate-900"
          >
            Home Route
          </Link>
          <Link
            href={`/${locale}/design-preview/overview`}
            className="inline-flex h-11 items-center gap-2 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white transition-colors duration-200 hover:bg-slate-800"
          >
            Open Overview
            <ArrowUpRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {PREVIEW_SECTIONS.map((section) => (
          <Link
            key={section.key}
            href={`/${locale}/design-preview/${section.key}`}
            className="app-surface block px-6 py-6 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_28px_70px_-48px_rgba(15,23,42,0.18)]"
          >
            <p className="app-page-kicker">{section.title}</p>
            <h2 className="mt-4 text-xl font-semibold tracking-[-0.02em] text-slate-900">
              {section.title}
            </h2>
            <p className="mt-3 text-sm leading-7 text-stone-600">{section.desc}</p>
            <p className="mt-5 text-xs font-semibold uppercase tracking-[0.14em] text-stone-500">
              {tCommon("next")} →
            </p>
          </Link>
        ))}
      </section>
    </>
  )
}
