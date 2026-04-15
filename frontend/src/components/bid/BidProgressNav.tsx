"use client"

import { memo } from "react"
import { useTranslations } from "next-intl"
import { useQuery } from "@tanstack/react-query"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { bidPlanService } from "@/services/bid-plan"
import type { BidStep } from "@/types/bid"

const STEPS: { key: BidStep; icon: string }[] = [
  { key: "upload", icon: "📄" },
  { key: "overview", icon: "📋" },
  { key: "plan", icon: "📅" },
  { key: "writing", icon: "✍️" },
  { key: "review", icon: "✅" },
]

export const BidProgressNav = memo(function BidProgressNav() {
  const { projectId, currentStep, completedSteps, goToStep } = useBidWorkspaceStore()
  const t = useTranslations("workspace")

  const { data: tasks } = useQuery({
    queryKey: ["bid-plan-tasks", projectId],
    queryFn: () => bidPlanService.listTasks(projectId!),
    enabled: !!projectId,
    staleTime: 30_000,
    retry: false,
  })

  const taskList = Array.isArray(tasks) ? tasks : []
  const totalCount = taskList.length
  const completedCount = taskList.filter((t) => t.status === "completed").length
  const pendingCount = totalCount - completedCount
  const pct = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0
  const hasTasks = totalCount > 0
  const allDone = hasTasks && pendingCount === 0

  return (
    <nav className="app-section-frame w-[240px] shrink-0 overflow-y-auto px-4 py-5">
      <p className="app-page-kicker mb-3">{t("title")}</p>

      {/* ── 投标计划持久化卡片 ── */}
      <button
        onClick={() => goToStep("plan")}
        className={`mb-4 w-full rounded-2xl border px-3.5 py-3 text-left transition-all duration-200 ${
          allDone
            ? "border-emerald-200 bg-emerald-50 hover:bg-emerald-100"
            : hasTasks
              ? "border-amber-200 bg-amber-50 hover:bg-amber-100"
              : "border-slate-200 bg-slate-50 hover:bg-slate-100"
        }`}
      >
        <div className="flex items-center justify-between gap-2">
          <span className="text-sm font-semibold text-slate-800">
            📅 {t("planCard.title")}
          </span>
          {hasTasks && (
            <span
              className={`rounded-full px-2 py-0.5 text-[11px] font-semibold leading-none ${
                allDone
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-orange-100 text-orange-700"
              }`}
            >
              {allDone
                ? t("planCard.allDone")
                : t("planCard.pendingCount", { count: pendingCount })}
            </span>
          )}
        </div>

        {hasTasks ? (
          <>
            {/* 进度条 */}
            <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  allDone ? "bg-emerald-500" : "bg-amber-500"
                }`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <p className="mt-1.5 text-[11px] text-slate-500">
              {t("planCard.progress", { completed: completedCount, total: totalCount })}
            </p>
          </>
        ) : (
          <p className="mt-1 text-[11px] text-slate-400">{t("planCard.noPlan")}</p>
        )}
      </button>

      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
        {t("stepsTitle")}
      </h3>
      <ol className="space-y-1.5">
        {STEPS.map((step, index) => {
          const isActive = currentStep === step.key
          const isCompleted = completedSteps.includes(step.key)
          const allEarlierCompleted = STEPS.slice(0, index).every((s) =>
            completedSteps.includes(s.key)
          )
          const canNavigate = isCompleted || isActive || index === 0 || allEarlierCompleted

          return (
            <li key={step.key}>
              <button
                onClick={() => canNavigate && goToStep(step.key)}
                disabled={!canNavigate}
                className={`flex w-full items-center gap-3 rounded-2xl border px-3 py-3 text-sm transition-all duration-200 ${
                  isActive
                    ? "border-slate-900 bg-slate-900 text-white font-medium shadow-[0_20px_36px_-28px_rgba(15,23,42,0.75)]"
                    : isCompleted
                      ? "border-emerald-100 bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
                      : canNavigate
                        ? "border-transparent text-foreground hover:border-stone-200 hover:bg-stone-100"
                        : "border-transparent text-muted-foreground/50 cursor-not-allowed"
                }`}
              >
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-white/70 text-xs">
                  {isCompleted ? "✓" : step.icon}
                </span>
                <span className="flex-1 text-left">{t(`steps.${step.key}`)}</span>
                <span className="text-[10px] uppercase tracking-[0.12em] opacity-70">
                  {index + 1}
                </span>
              </button>
            </li>
          )
        })}
      </ol>
    </nav>
  )
})
