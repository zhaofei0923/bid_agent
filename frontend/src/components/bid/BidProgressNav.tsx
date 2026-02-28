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
    <nav className="w-[220px] shrink-0 border-r bg-muted/30 p-4">
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
                className={`w-full flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors ${
                  isActive
                    ? "bg-primary text-primary-foreground font-medium"
                    : isCompleted
                      ? "bg-green-50 text-green-700 hover:bg-green-100 dark:bg-green-950 dark:text-green-400"
                      : canNavigate
                        ? "text-foreground hover:bg-muted"
                        : "text-muted-foreground/50 cursor-not-allowed"
                }`}
              >
                <span className="flex h-6 w-6 items-center justify-center rounded-full text-xs">
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
