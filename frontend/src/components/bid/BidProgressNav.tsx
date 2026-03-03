"use client"

import { memo } from "react"
import { useTranslations } from "next-intl"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import type { BidStep } from "@/types/bid"

const STEPS: { key: BidStep; icon: string }[] = [
  { key: "upload", icon: "📄" },
  { key: "overview", icon: "📋" },
  { key: "analysis", icon: "🔍" },
  { key: "plan", icon: "📅" },
  { key: "writing", icon: "✍️" },
  { key: "review", icon: "✅" },
  { key: "tracking", icon: "📊" },
]

export const BidProgressNav = memo(function BidProgressNav() {
  const { currentStep, completedSteps, goToStep } = useBidWorkspaceStore()
  const t = useTranslations("workspace")

  return (
    <nav className="app-section-frame w-[240px] shrink-0 overflow-y-auto px-4 py-5">
      <p className="app-page-kicker mb-3">{t("title")}</p>
      <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
        {t("stepsTitle")}
      </h3>
      <ol className="space-y-1.5">
        {STEPS.map((step, index) => {
          const isActive = currentStep === step.key
          const isCompleted = completedSteps.includes(step.key)
          const canNavigate = isCompleted || isActive || index === 0

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
