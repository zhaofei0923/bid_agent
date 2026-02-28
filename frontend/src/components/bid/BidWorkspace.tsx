"use client"

import { memo } from "react"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { UploadStep } from "./UploadStep"
import { OverviewStep } from "./OverviewStep"
import { AnalysisStep } from "./AnalysisStep"
import { PlanStep } from "./PlanStep"
import { QAStep } from "./QAStep"
import { QualityReviewPanel } from "./quality/QualityReviewPanel"
import { TrackingStep } from "./TrackingStep"
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
    analysis: <AnalysisStep projectId={projectId} />,
    plan: <PlanStep projectId={projectId} />,
    writing: <QAStep projectId={projectId} />,
    review: <QualityReviewPanel projectId={projectId} />,
    tracking: <TrackingStep projectId={projectId} />,
  }

  return (
    <div className="flex-1 overflow-y-auto p-6">
      {stepComponents[currentStep] || (
        <div className="text-center text-muted-foreground py-12">
          {t("unknownStep")}
        </div>
      )}
    </div>
  )
})
