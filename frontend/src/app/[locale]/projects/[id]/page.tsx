"use client"

import { use } from "react"
import { useTranslations } from "next-intl"
import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { projectService } from "@/services/projects"
import { bidPlanService } from "@/services/bid-plan"
import { bidAnalysisService } from "@/services/bid-analysis"
import { formatDate } from "@/lib/utils"
import { MainLayout } from "@/components/layout/MainLayout"
import { AppPageShell } from "@/components/layout/AppPageShell"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

/**
 * Defensively extract submission deadline from BidAnalysis.key_dates.
 * Handles both flat { submission_deadline: "2026-05-01" } and
 * array { dates: [{ type: "submission_deadline", date: "..." }] } shapes.
 */
function extractDeadline(keyDates: Record<string, unknown> | null | undefined): string | null {
  if (!keyDates) return null
  const DATE_RE = /\d{4}-\d{2}-\d{2}/
  for (const key of ["submission_deadline", "bid_submission_deadline", "deadline", "submission_date"]) {
    const v = keyDates[key]
    if (typeof v === "string" && DATE_RE.test(v)) return v
  }
  const dates = keyDates.dates
  if (Array.isArray(dates)) {
    // Try to find submission deadline specifically
    for (const d of dates as Array<Record<string, unknown>>) {
      const isDeadline =
        String(d.type ?? "").includes("submission") ||
        String(d.label ?? "").includes("截止") ||
        String(d.type ?? "").includes("deadline")
      const ds = String(d.date ?? d.value ?? d.deadline ?? "")
      if (isDeadline && DATE_RE.test(ds)) return ds.match(DATE_RE)![0]
    }
    // Fallback: first valid date in array
    for (const d of dates as Array<Record<string, unknown>>) {
      const ds = String(d.date ?? d.value ?? "")
      if (DATE_RE.test(ds)) return ds.match(DATE_RE)![0]
    }
  }
  return null
}

/** Whole days remaining until deadline (negative = overdue). */
function calcDaysLeft(dateStr: string | null): number | null {
  if (!dateStr) return null
  const dl = new Date(dateStr)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  dl.setHours(0, 0, 0, 0)
  return Math.ceil((dl.getTime() - today.getTime()) / 86_400_000)
}

function fmtDeadline(dateStr: string): string {
  const [y, m, d] = dateStr.split("-").map(Number)
  return `${y}年${m}月${d}日`
}

export default function ProjectDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const t = useTranslations("projects")
  const tc = useTranslations("common")
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"

  const { data: project, isLoading } = useQuery({
    queryKey: ["project", id],
    queryFn: () => projectService.getById(id),
  })

  const { data: plan } = useQuery({
    queryKey: ["bid-plan", id],
    queryFn: () => bidPlanService.getByProject(id),
    enabled: !!id,
    retry: false,
  })

  const { data: analysis } = useQuery({
    queryKey: ["bid-analysis", id],
    queryFn: () => bidAnalysisService.getByProject(id),
    enabled: !!id,
    retry: false,
  })

  if (isLoading) return <MainLayout><div className="p-8 text-center">{tc("loading")}</div></MainLayout>
  if (!project) return <MainLayout><div className="p-8 text-center">{t("notFound")}</div></MainLayout>

  // ── Task stats ────────────────────────────────────────────────
  const hasPlan = !!plan
  const totalTasks = plan?.total_tasks ?? 0
  const completedTasks = plan?.completed_tasks ?? 0
  const pendingTasks = totalTasks - completedTasks
  const taskPct = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0

  // ── Deadline & countdown ──────────────────────────────────────
  const deadlineStr = extractDeadline(analysis?.key_dates)
  const daysLeft = calcDaysLeft(deadlineStr)

  const daysColor =
    daysLeft === null ? "text-muted-foreground" :
    daysLeft < 0     ? "text-rose-600" :
    daysLeft <= 7    ? "text-rose-600" :
    daysLeft <= 14   ? "text-amber-600" :
                       "text-emerald-600"

  const daysBg =
    daysLeft === null ? "" :
    daysLeft < 0     ? "bg-rose-50" :
    daysLeft <= 7    ? "bg-rose-50" :
    daysLeft <= 14   ? "bg-amber-50" :
                       "bg-emerald-50"

  const daysText =
    daysLeft === null  ? t("noDeadline") :
    daysLeft < 0       ? t("overdue") :
    daysLeft === 0     ? t("daysToday") :
                         `${daysLeft} ${t("daysLeftUnit")}`

  return (
    <MainLayout>
      <AppPageShell
        eyebrow={t("createdAt")}
        title={project.name}
        description={
          project.description ||
          t("createdOn", { date: formatDate(project.created_at) })
        }
        actions={
          <>
            <Button asChild variant="outline">
              <Link href={`/${locale}/projects`}>{tc("backToList")}</Link>
            </Button>
            <Button asChild>
              <Link href={`/${locale}/projects/${id}/workspace`}>
                {t("openWorkspace")}
              </Link>
            </Button>
          </>
        }
      >
        <div className="app-section-frame px-6 py-8 sm:px-8">
          <div className="flex flex-wrap items-center gap-3">
            <Badge variant="secondary">{project.status}</Badge>
            <span className="text-sm font-medium text-stone-500">
              {t("createdOn", { date: formatDate(project.created_at) })}
            </span>
          </div>

          {/* ── 四格统计卡片 ── */}
          <div className="mt-6 grid gap-4 grid-cols-2 md:grid-cols-4">

            {/* 1. 已完成任务 */}
            <div className="app-surface-muted px-5 py-5">
              <p className="app-detail-label">{t("taskCompleted")}</p>
              {hasPlan ? (
                <>
                  <p className="app-detail-value mt-2">
                    <span className="text-emerald-600">{completedTasks}</span>
                    <span className="text-muted-foreground text-lg font-normal"> / {totalTasks}</span>
                  </p>
                  <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
                    <div
                      className="h-full rounded-full bg-emerald-500 transition-all duration-500"
                      style={{ width: `${taskPct}%` }}
                    />
                  </div>
                  <p className="mt-1 text-[11px] text-muted-foreground">{taskPct}%</p>
                </>
              ) : (
                <p className="app-detail-value mt-2 text-muted-foreground text-base">{t("noPlan")}</p>
              )}
            </div>

            {/* 2. 待处理任务 */}
            <div className={`app-surface-muted px-5 py-5 ${hasPlan && pendingTasks > 0 ? "bg-amber-50/60" : ""}`}>
              <p className="app-detail-label">{t("pendingTasks")}</p>
              {hasPlan ? (
                <>
                  <p className={`app-detail-value mt-2 ${pendingTasks > 0 ? "text-amber-600" : "text-emerald-600"}`}>
                    {pendingTasks}
                  </p>
                  <p className="mt-1 text-[11px] text-muted-foreground">{t("tasksUnit")}</p>
                </>
              ) : (
                <p className="app-detail-value mt-2 text-muted-foreground text-base">—</p>
              )}
            </div>

            {/* 3. 投标截止日期 */}
            <div className="app-surface-muted px-5 py-5">
              <p className="app-detail-label">{t("bidDeadline")}</p>
              <p className="app-detail-value mt-2">
                {deadlineStr
                  ? fmtDeadline(deadlineStr)
                  : <span className="text-muted-foreground text-base">{t("noDeadline")}</span>}
              </p>
            </div>

            {/* 4. 距截止还有 */}
            <div className={`app-surface-muted px-5 py-5 ${daysBg}`}>
              <p className="app-detail-label">{t("daysLeft")}</p>
              <p className={`app-detail-value mt-2 ${daysColor}`}>{daysText}</p>
              {daysLeft !== null && daysLeft > 0 && (
                <p className="mt-1 text-[11px] text-muted-foreground">{deadlineStr}</p>
              )}
            </div>
          </div>

          {/* ── 整体进度条 ── */}
          <div className="mt-6">
            <div className="mb-1.5 flex items-center justify-between text-xs text-muted-foreground">
              <span>{t("progress")}</span>
              <span>{project.progress}%</span>
            </div>
            <div className="app-progress-track">
              <div
                className="app-progress-fill transition-all"
                style={{ width: `${project.progress}%` }}
              />
            </div>
          </div>
        </div>
      </AppPageShell>
    </MainLayout>
  )
}
