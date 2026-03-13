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

// Shared Markdown component overrides for consistent typography
const markdownComponents = {
  h1: ({ children }: { children?: React.ReactNode }) => (
    <h1 className="mt-6 mb-3 border-b border-slate-200 pb-2 text-base font-bold text-slate-900 first:mt-0">
      {children}
    </h1>
  ),
  h2: ({ children }: { children?: React.ReactNode }) => (
    <h2 className="mt-6 mb-2 border-b border-slate-200 pb-1 text-[15px] font-semibold text-slate-800 first:mt-0">
      {children}
    </h2>
  ),
  h3: ({ children }: { children?: React.ReactNode }) => (
    <h3 className="mt-4 mb-1.5 text-sm font-semibold text-slate-800">
      {children}
    </h3>
  ),
  h4: ({ children }: { children?: React.ReactNode }) => (
    <h4 className="mt-3 mb-1 text-sm font-medium text-slate-700">
      {children}
    </h4>
  ),
  p: ({ children }: { children?: React.ReactNode }) => (
    <p className="mb-2.5 text-[13px] leading-relaxed text-slate-600">
      {children}
    </p>
  ),
  ul: ({ children }: { children?: React.ReactNode }) => (
    <ul className="mb-2.5 list-disc pl-5 text-[13px] text-slate-600">
      {children}
    </ul>
  ),
  ol: ({ children }: { children?: React.ReactNode }) => (
    <ol className="mb-2.5 list-decimal pl-5 text-[13px] text-slate-600">
      {children}
    </ol>
  ),
  li: ({ children }: { children?: React.ReactNode }) => (
    <li className="mb-1 leading-relaxed">{children}</li>
  ),
  strong: ({ children }: { children?: React.ReactNode }) => (
    <strong className="font-semibold text-slate-800">{children}</strong>
  ),
  blockquote: ({ children }: { children?: React.ReactNode }) => (
    <blockquote className="my-3 border-l-4 border-slate-300 bg-slate-50 py-2 pl-4 pr-2 text-[13px] italic text-slate-600">
      {children}
    </blockquote>
  ),
  table: ({ children }: { children?: React.ReactNode }) => (
    <div className="my-3 overflow-x-auto">
      <table className="min-w-full border-collapse text-[13px] text-slate-700">
        {children}
      </table>
    </div>
  ),
  th: ({ children }: { children?: React.ReactNode }) => (
    <th className="border border-slate-200 bg-slate-50 px-3 py-1.5 text-left text-[13px] font-semibold text-slate-800">
      {children}
    </th>
  ),
  td: ({ children }: { children?: React.ReactNode }) => (
    <td className="border border-slate-200 px-3 py-1.5 text-left">
      {children}
    </td>
  ),
} as const

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
                components={markdownComponents}
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
