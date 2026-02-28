"use client"

import { memo } from "react"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { useDocuments } from "@/hooks/use-documents"
import { useBidAnalysis, useTriggerAnalysis } from "@/hooks/use-bid-analysis"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useTranslations } from "next-intl"

interface OverviewStepProps {
  projectId: string
}

export const OverviewStep = memo(function OverviewStep({
  projectId,
}: OverviewStepProps) {
  const { completeStep, goToStep } = useBidWorkspaceStore()
  const t = useTranslations("bid")
  const { data: documents, isLoading: docsLoading } = useDocuments(projectId)
  const { data: analysis, isLoading: analysisLoading } = useBidAnalysis(projectId)

  const handleNext = () => {
    completeStep("overview")
    goToStep("analysis")
  }

  if (docsLoading || analysisLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">{t("overview.title")}</h2>
        <p className="text-muted-foreground text-sm mt-1">
          {t("overview.subtitle")}
        </p>
      </div>

      {/* Document structure */}
      <Card>
        <CardHeader className="pb-2">
          <h3 className="text-sm font-semibold">{t("overview.docStructure")}</h3>
        </CardHeader>
        <CardContent>
          {documents && documents.length > 0 ? (
            <div className="space-y-2">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between py-2 border-b last:border-0"
                >
                  <div>
                    <p className="text-sm font-medium">
                      {doc.file_name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {doc.file_type?.toUpperCase()} ·{" "}
                      {Math.round(doc.file_size / 1024)} KB
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">{t("overview.noDocs")}</p>
          )}
        </CardContent>
      </Card>

      {/* Quick analysis summary */}
      {analysis && (
        <Card>
          <CardHeader className="pb-2">
            <h3 className="text-sm font-semibold">{t("overview.aiSummary")}</h3>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              {analysis.bid_type && (
                <div>
                  <p className="text-xs text-muted-foreground">{t("overview.bidType")}</p>
                  <p className="text-sm font-medium">{analysis.bid_type}</p>
                </div>
              )}
              {analysis.key_dates && (
                <div>
                  <p className="text-xs text-muted-foreground">{t("overview.keyDates")}</p>
                  <p className="text-sm font-medium">
                    {t("overview.datesIdentified", { count: Object.keys(analysis.key_dates).length })}
                  </p>
                </div>
              )}
              {analysis.qualification_requirements && (
                <div>
                  <p className="text-xs text-muted-foreground">{t("overview.qualificationReqs")}</p>
                  <p className="text-sm font-medium">{t("overview.extracted")}</p>
                </div>
              )}
              {analysis.evaluation_criteria && (
                <div>
                  <p className="text-xs text-muted-foreground">{t("overview.evaluationCriteria")}</p>
                  <p className="text-sm font-medium">{t("overview.extracted")}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex justify-end">
        <Button onClick={handleNext}>{t("overview.nextStep")}</Button>
      </div>
    </div>
  )
})
