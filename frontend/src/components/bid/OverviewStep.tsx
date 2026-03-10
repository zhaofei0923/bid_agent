"use client"

import { memo, useEffect } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
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
        <CardContent>
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
            // Combined overview ready — render as structured Markdown
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  h2: ({ children }) => (
                    <h2 className="mt-5 mb-2 border-b border-slate-200 pb-1 text-sm font-semibold text-slate-800 first:mt-0">
                      {children}
                    </h2>
                  ),
                  p: ({ children }) => (
                    <p className="mb-3 text-sm leading-relaxed text-slate-700">
                      {children}
                    </p>
                  ),
                  ul: ({ children }) => (
                    <ul className="mb-3 list-disc pl-5 text-sm text-slate-700">
                      {children}
                    </ul>
                  ),
                  li: ({ children }) => (
                    <li className="mb-1 leading-relaxed">{children}</li>
                  ),
                  strong: ({ children }) => (
                    <strong className="font-semibold text-slate-800">{children}</strong>
                  ),
                }}
              >
                {project!.combined_ai_overview!}
              </ReactMarkdown>
            </div>
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
        </CardContent>
      </Card>

      {hasCombinedOverview && (
        <div className="flex justify-end pt-2">
          <Button onClick={handleNext}>
            {t("overview.nextStep")}
          </Button>
        </div>
      )}
    </div>
  )
})
