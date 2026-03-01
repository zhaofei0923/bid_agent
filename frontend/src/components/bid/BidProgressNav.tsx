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
    <nav className="app-surface mr-4 w-[240px] shrink-0 overflow-y-auto px-4 py-5">
      <h3 className="mb-4 text-sm font-semibold text-muted-foreground uppercase tracking-wider">
        {t("stepsTitle")}
      </h3>
      <ol className="space-y-1">
        {STEPS.map((step, index) => {
          const isActive = currentStep === step.key
          const isCompleted = completedSteps.includes(step.key)
          const canNavigate = isCompleted || isActive || index === 0

          return (
            <li key={step.key}>
              <button
                onClick={() => canNavigate && goToStep(step.key)}
                disabled={!canNavigate}
                className={`flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-sm transition-colors ${
                  isActive
                    ? "bg-slate-900 text-white font-medium"
                    : isCompleted
                      ? "bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
                      : canNavigate
                        ? "text-foreground hover:bg-stone-100"
                        : "text-muted-foreground/50 cursor-not-allowed"
                }`}
              >
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-white/70 text-xs">
                  {isCompleted ? "✓" : step.icon}
                </span>
                <span>{t(`steps.${step.key}`)}</span>
              </button>
            </li>
          )
        })}
      </ol>
    </nav>
  )
})
