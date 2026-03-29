"use client"

import { memo } from "react"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { UploadStep } from "./UploadStep"
import { OverviewStep } from "./OverviewStep"
import { PlanStep } from "./PlanStep"
import { ChecklistStep } from "./ChecklistStep"
import { DocumentReviewPanel } from "./review/DocumentReviewPanel"
import { useTranslations } from "next-intl"

interface BidWorkspaceProps {
  projectId: string
}

export const BidWorkspace = memo(function BidWorkspace({
  projectId,
}: BidWorkspaceProps) {
  const { currentStep } = useBidWorkspaceStore()
  const t = useTranslations("workspace")

  const stepComponents: Record<string, React.ReactNode> = {
    upload: <UploadStep projectId={projectId} />,
    overview: <OverviewStep projectId={projectId} />,
    plan: <PlanStep projectId={projectId} />,
    writing: <ChecklistStep projectId={projectId} />,
    review: <DocumentReviewPanel projectId={projectId} />,
  }
  const currentStepContent = stepComponents[currentStep]

  return (
    <div className="app-section-frame flex flex-1 flex-col overflow-hidden">
      <div className="border-b border-stone-200 px-6 py-5 sm:px-8">
        <p className="app-page-kicker">{t("stepsTitle")}</p>
        <h2 className="mt-3 text-2xl font-semibold tracking-[-0.025em] text-slate-900">
          {currentStepContent ? t(`steps.${currentStep}`) : t("unknownStep")}
        </h2>
      </div>
      <div className="flex-1 overflow-y-auto px-6 py-6 sm:px-8">
        {currentStepContent || (
          <div className="py-12 text-center text-muted-foreground">
            {t("unknownStep")}
          </div>
        )}
      </div>
    </div>
  )
})
