"use client"

import { memo, useEffect } from "react"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { useDocuments, useAnalyzeCombined } from "@/hooks/use-documents"
import { useProject } from "@/hooks/use-projects"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useTranslations } from "next-intl"

// Backend statuses
const SUCCESS_STATUSES = new Set(["processed", "completed"])
const ACTIVE_STATUSES = new Set(["pending", "processing"])

// ──────────────────────────────────────────────
// Main component
// ──────────────────────────────────────────────

interface OverviewStepProps {
  projectId: string
}

export const OverviewStep = memo(function OverviewStep({
  projectId,
}: OverviewStepProps) {
  const { completeStep, goToStep } = useBidWorkspaceStore()
  const t = useTranslations("bid")

  // Documents — poll until all are processed
  const { data: documents, isLoading: docsLoading } = useDocuments(projectId)

  // Project — poll until combined_ai_overview appears
  const { data: project, isLoading: projectLoading } = useProject(projectId, true)

  const analyzeCombined = useAnalyzeCombined(projectId)

  const allDone =
    !!documents &&
    documents.length > 0 &&
    documents.every((d) => SUCCESS_STATUSES.has(d.status))

  const anyProcessing =
    !!documents && documents.some((d) => ACTIVE_STATUSES.has(d.status))

  const hasCombinedOverview = !!project?.combined_ai_overview

  // Auto-trigger combined analysis once all docs are processed and overview is missing
  useEffect(() => {
    if (
      allDone &&
      !hasCombinedOverview &&
      !analyzeCombined.isPending &&
      !analyzeCombined.isSuccess
    ) {
      analyzeCombined.mutate()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allDone, hasCombinedOverview])

  const handleNext = () => {
    completeStep("overview")
    goToStep("analysis")
  }

  if (docsLoading || projectLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-60 w-full" />
      </div>
    )
  }

  if (!documents || documents.length === 0) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        {t("overview.noDocs")}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="pb-2">
          <h3 className="text-sm font-semibold">{t("overview.aiReading")}</h3>
        </CardHeader>
        <CardContent className="space-y-4">
          {anyProcessing ? (
            // Still parsing PDFs
            <div className="space-y-2">
              <p className="text-xs text-muted-foreground animate-pulse">
                ⏳ {t("overview.processingHint")}
              </p>
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-4/6" />
            </div>
          ) : hasCombinedOverview ? (
            // Combined overview ready
            <p className="whitespace-pre-line text-sm leading-relaxed text-slate-700">
              {project!.combined_ai_overview}
            </p>
          ) : (
            // All processed but waiting for LLM analysis
            <div className="space-y-2">
              <p className="text-xs text-muted-foreground animate-pulse">
                ⏳ {t("overview.generatingOverview")}
              </p>
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-4/6" />
            </div>
          )}

          {/* Reading tips callout */}
          {hasCombinedOverview && project?.combined_ai_reading_tips && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
              <p className="mb-1 text-xs font-semibold text-amber-700">
                💡 {t("overview.aiReadingTips")}
              </p>
              <p className="whitespace-pre-line text-sm leading-relaxed text-amber-800">
                {project.combined_ai_reading_tips}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-end pt-2">
        <Button onClick={handleNext} disabled={anyProcessing}>
          {t("overview.nextStep")}
        </Button>
      </div>
    </div>
  )
})
