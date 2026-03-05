"use client"

import { memo, useEffect } from "react"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { useDocuments, useAnalyzeDocument } from "@/hooks/use-documents"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useTranslations } from "next-intl"
import type { ProjectDocument } from "@/types"

// ──────────────────────────────────────────────
// Sub-components
// ──────────────────────────────────────────────

// Backend statuses: pending → processing → processed (success) | error (failure)
const SUCCESS_STATUSES = new Set(["processed", "completed"])
const ACTIVE_STATUSES = new Set(["pending", "processing"])

function DocDetailPanel({
  projectId,
  doc,
}: {
  projectId: string
  doc: ProjectDocument
}) {
  const t = useTranslations("bid")
  const isProcessing = ACTIVE_STATUSES.has(doc.status)
  const hasFailed = doc.status === "error" || doc.status === "failed"
  const isSuccess = SUCCESS_STATUSES.has(doc.status)
  const needsAiAnalysis = isSuccess && doc.ai_overview === null
  const analyzeMutation = useAnalyzeDocument(projectId)

  // Auto-trigger AI analysis for processed docs that have no overview yet
  useEffect(() => {
    if (needsAiAnalysis && !analyzeMutation.isPending && !analyzeMutation.isSuccess) {
      analyzeMutation.mutate(doc.id)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doc.id, needsAiAnalysis])

  return (
    <div className="space-y-5">
      {/* Block B: AI Interpretation */}
      <Card>
        <CardHeader className="pb-2">
          <h3 className="text-sm font-semibold">{t("overview.aiReading")}</h3>
        </CardHeader>
        <CardContent className="space-y-4">
          {hasFailed ? (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3">
              <p className="text-sm font-medium text-red-700">{t("overview.failed")}</p>
              {doc.error_message && (
                <p className="mt-1 text-xs text-red-600">{doc.error_message}</p>
              )}
            </div>
          ) : isProcessing ? (
            <div className="space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-4/6" />
            </div>
          ) : needsAiAnalysis || analyzeMutation.isPending ? (
            <div className="space-y-2">
              <p className="text-xs text-muted-foreground animate-pulse">⏳ {t("overview.generatingOverview")}</p>
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-4/6" />
            </div>
          ) : doc.ai_overview ? (
            <p className="whitespace-pre-line text-sm leading-relaxed text-slate-700">
              {doc.ai_overview}
            </p>
          ) : (
            <p className="text-sm text-muted-foreground">{t("overview.noOverview")}</p>
          )}

          {/* Reading tips callout */}
          {!isProcessing && doc.ai_reading_tips && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
              <p className="mb-1 text-xs font-semibold text-amber-700">
                💡 {t("overview.aiReadingTips")}
              </p>
              <p className="whitespace-pre-line text-sm leading-relaxed text-amber-800">
                {doc.ai_reading_tips}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

    </div>
  )
}

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
  const { data: documents, isLoading: docsLoading } = useDocuments(projectId)

  const handleNext = () => {
    completeStep("overview")
    goToStep("analysis")
  }

  if (docsLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-16 w-full" />
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
      {/* per-document AI detail */}
      {documents.map((doc) => (
        <DocDetailPanel key={doc.id} projectId={projectId} doc={doc} />
      ))}

      <div className="flex justify-end pt-2">
        <Button onClick={handleNext}>{t("overview.nextStep")}</Button>
      </div>
    </div>
  )
})
