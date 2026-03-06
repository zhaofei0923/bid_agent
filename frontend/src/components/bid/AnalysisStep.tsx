"use client"

import { memo } from "react"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { useBidAnalysis, useTriggerAnalysis } from "@/hooks/use-bid-analysis"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useTranslations } from "next-intl"

function _extractErrorMessage(error: unknown): string {
  if (!error) return "未知错误"
  const axiosErr = error as { response?: { data?: { message?: string; detail?: string }; status?: number } }
  if (axiosErr.response?.status === 402) return "积分不足，无法执行分析（需要 20 积分）"
  const msg = axiosErr.response?.data?.message ?? axiosErr.response?.data?.detail
  if (msg) return msg
  const baseErr = error as { message?: string }
  if (baseErr.message?.includes("timeout")) return "分析超时，请稍后重试"
  return baseErr.message ?? "请求失败，请稍后重试"
}

const ANALYSIS_DIMENSIONS = [
  { key: "qualification", icon: "📋" },
  { key: "evaluation", icon: "📊" },
  { key: "key_dates", icon: "📅" },
  { key: "submission", icon: "📦" },
  { key: "bds_modification", icon: "📝" },
  { key: "methodology", icon: "🔬" },
  { key: "commercial", icon: "💰" },
  { key: "risk_assessment", icon: "⚠️" },
]

interface AnalysisStepProps {
  projectId: string
}

export const AnalysisStep = memo(function AnalysisStep({
  projectId,
}: AnalysisStepProps) {
  const { completeStep, goToStep } = useBidWorkspaceStore()
  const t = useTranslations("bid")
  const { data: analysis, isLoading } = useBidAnalysis(projectId)
  const triggerMutation = useTriggerAnalysis(projectId)

  const handleRunAnalysis = () => {
    triggerMutation.mutate({})
  }

  const handleRunSingleAnalysis = (step: string) => {
    triggerMutation.mutate({ steps: [step], force_refresh: true })
  }

  const handleNext = () => {
    completeStep("analysis")
    goToStep("plan")
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-24 w-full" />
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">{t("analysis.title")}</h2>
          <p className="text-muted-foreground text-sm mt-1">
            {t("analysis.subtitle")}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRunAnalysis}
            disabled={triggerMutation.isPending}
          >
            {triggerMutation.isPending ? t("analysis.analyzing") : t("analysis.reanalyze")}
          </Button>
          {triggerMutation.isError && (
            <p className="text-xs text-red-500">
              ❌ {_extractErrorMessage(triggerMutation.error)}
            </p>
          )}
        </div>
      </div>

      {!analysis ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground mb-4">{t("analysis.noAnalysis")}</p>
            <Button onClick={handleRunAnalysis} disabled={triggerMutation.isPending}>
              {triggerMutation.isPending ? t("analysis.analyzing") : t("analysis.startAnalysis")}
            </Button>
            {triggerMutation.isPending && (
              <p className="mt-3 text-xs text-muted-foreground animate-pulse">
                ⏳ {t("analysis.analyzingHint")}
              </p>
            )}
            {triggerMutation.isError && (
              <p className="mt-3 text-xs text-red-500">
                ❌ {_extractErrorMessage(triggerMutation.error)}
              </p>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {ANALYSIS_DIMENSIONS.map((dim) => {
            const data =
              analysis[dim.key as keyof typeof analysis] as Record<
                string,
                unknown
              > | null
            const hasData = data && Object.keys(data).length > 0

            return (
              <Card key={dim.key}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span>{dim.icon}</span>
                      <h3 className="text-sm font-semibold">{t(`analysis.dimensions.${dim.key}`)}</h3>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={hasData ? "default" : "secondary"}>
                        {hasData ? t("analysis.completed") : t("analysis.pending")}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 px-2 text-xs"
                        onClick={() => handleRunSingleAnalysis(dim.key)}
                        disabled={triggerMutation.isPending}
                      >
                        {triggerMutation.isPending ? "..." : t("analysis.reanalyze")}
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {hasData ? (
                    <pre className="text-xs text-muted-foreground whitespace-pre-wrap max-h-32 overflow-y-auto">
                      {JSON.stringify(data, null, 2).slice(0, 300)}
                      {JSON.stringify(data, null, 2).length > 300 ? "..." : ""}
                    </pre>
                  ) : (
                    <p className="text-xs text-muted-foreground">
                      {t("analysis.clickToRun")}
                    </p>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {analysis && (
        <div className="flex justify-end">
          <Button onClick={handleNext}>{t("analysis.nextStep")}</Button>
        </div>
      )}
    </div>
  )
})
