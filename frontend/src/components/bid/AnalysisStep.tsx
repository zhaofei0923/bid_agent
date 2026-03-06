"use client"

import { memo, useState } from "react"
import { ChevronDown, ChevronUp } from "lucide-react"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { useBidAnalysis, useTriggerAnalysis } from "@/hooks/use-bid-analysis"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useTranslations } from "next-intl"
import { AnalysisDimView } from "./AnalysisDimView"
import type { BidAnalysis } from "@/types/bid"

function _extractErrorMessage(error: unknown): string {
  if (!error) return "未知错误"
  const axiosErr = error as {
    response?: {
      data?: {
        message?: string
        detail?: string
        error?: { message?: string; code?: string }
      }
      status?: number
    }
    message?: string
  }
  const status = axiosErr.response?.status
  // Try nested data.error.message (BidAgentException format)
  const nestedMsg = axiosErr.response?.data?.error?.message
  const flatMsg = axiosErr.response?.data?.message ?? axiosErr.response?.data?.detail
  const msg = nestedMsg ?? flatMsg
  if (status === 402 || axiosErr.response?.data?.error?.code === "INSUFFICIENT_CREDITS") {
    return msg ?? "积分不足，无法执行分析（需要 20 积分）"
  }
  if (msg) return msg
  if (axiosErr.message?.includes("timeout")) return "分析超时，请稍后重试"
  return axiosErr.message ?? "请求失败，请稍后重试"
}

// dim key → actual BidAnalysis field name
const FIELD_MAP: Record<string, keyof BidAnalysis> = {
  qualification: "qualification_requirements",
  evaluation: "evaluation_criteria",
  key_dates: "key_dates",
  submission: "submission_checklist",
  bds_modification: "bds_modifications",
  methodology: "evaluation_methodology",
  commercial: "commercial_terms",
}

const ANALYSIS_DIMENSIONS = [
  { key: "qualification", icon: "📋" },
  { key: "evaluation", icon: "📊" },
  { key: "key_dates", icon: "📅" },
  { key: "submission", icon: "📦" },
  { key: "bds_modification", icon: "📝" },
  { key: "methodology", icon: "🔬" },
  { key: "commercial", icon: "💰" },
] as const

// One-line summary shown in collapsed header
function getDimSummary(key: string, data: Record<string, unknown>): string {
  const a = (v: unknown) => (Array.isArray(v) ? v : [])
  const r = (v: unknown): Record<string, unknown> =>
    v && typeof v === "object" && !Array.isArray(v) ? (v as Record<string, unknown>) : {}
  const n = (v: unknown) => (typeof v === "number" ? v : 0)
  const s = (v: unknown) => (typeof v === "string" ? v : "")
  switch (key) {
    case "qualification":
      return `${a(data.qualification_requirements).length} 类资质要求`
    case "evaluation": {
      const m = s(data.evaluation_method)
      const tw = n(data.technical_weight)
      return m ? `${m} · 技术权重 ${tw}%` : tw > 0 ? `技术权重 ${tw}%` : ""
    }
    case "key_dates": {
      const d = a(data.key_dates)
      const w = a(data.warnings)
      return `${d.length} 个关键日期${w.length > 0 ? `，⚠️ ${w.length} 条预警` : ""}`
    }
    case "submission":
      return `${a(data.required_documents).length} 份必交文件`
    case "bds_modification": {
      const mods = a(data.bds_modifications)
      const hi = mods.filter(
        (m) =>
          typeof m === "object" &&
          m !== null &&
          ["critical", "high"].includes(s((m as Record<string, unknown>).priority)),
      ).length
      return `${mods.length} 条修改${hi > 0 ? `，${hi} 条高优先级` : ""}`
    }
    case "methodology": {
      const em = r(data.evaluation_method)
      const sc = n(em.minimum_technical_score)
      return em.type ? `${s(em.type)} · 最低通过分 ${sc}` : ""
    }
    case "commercial": {
      const pt = r(data.payment_terms)
      return `${a(pt.payment_schedule).length} 个支付节点 · ${a(data.guarantees).length} 项担保`
    }
    default:
      return ""
  }
}

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
  const [expandedDims, setExpandedDims] = useState<Set<string>>(new Set())

  const toggleDim = (key: string) => {
    setExpandedDims((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

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
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">{t("analysis.title")}</h2>
          <p className="mt-1 text-sm text-muted-foreground">
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
            {triggerMutation.isPending
              ? t("analysis.analyzing")
              : t("analysis.reanalyze")}
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
            <p className="mb-4 text-muted-foreground">{t("analysis.noAnalysis")}</p>
            <Button
              onClick={handleRunAnalysis}
              disabled={triggerMutation.isPending}
            >
              {triggerMutation.isPending
                ? t("analysis.analyzing")
                : t("analysis.startAnalysis")}
            </Button>
            {triggerMutation.isPending && (
              <p className="mt-3 animate-pulse text-xs text-muted-foreground">
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
        <div className="space-y-4">
          {/* ── Risk Assessment — full-width at top, always expanded ── */}
          {(() => {
            const riskData = analysis.risk_assessment as Record<
              string,
              unknown
            > | null
            const hasData = riskData && Object.keys(riskData).length > 0
            return (
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span>⚠️</span>
                      <h3 className="text-sm font-semibold">
                        {t("analysis.dimensions.risk_assessment")}
                      </h3>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={hasData ? "default" : "secondary"}>
                        {hasData ? t("analysis.completed") : t("analysis.pending")}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 px-2 text-xs"
                        onClick={() => handleRunSingleAnalysis("risk_assessment")}
                        disabled={triggerMutation.isPending}
                      >
                        {triggerMutation.isPending ? "..." : t("analysis.reanalyze")}
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {hasData ? (
                    <AnalysisDimView dimension="risk_assessment" data={riskData} />
                  ) : (
                    <p className="text-xs text-muted-foreground">
                      {t("analysis.clickToRun")}
                    </p>
                  )}
                </CardContent>
              </Card>
            )
          })()}

          {/* ── Other 7 dimensions — full-width stacked, accordion ── */}
          {ANALYSIS_DIMENSIONS.map((dim) => {
            const field = FIELD_MAP[dim.key]
            const dimData = analysis[field] as Record<string, unknown> | null
            const hasData = dimData && Object.keys(dimData).length > 0
            const isExpanded = expandedDims.has(dim.key)
            const summary = hasData ? getDimSummary(dim.key, dimData) : ""

            return (
              <Card key={dim.key}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex min-w-0 flex-1 items-center gap-2">
                      <span>{dim.icon}</span>
                      <h3 className="shrink-0 text-sm font-semibold">
                        {t(`analysis.dimensions.${dim.key}`)}
                      </h3>
                      {summary && !isExpanded && (
                        <span className="truncate text-xs text-muted-foreground">
                          {summary}
                        </span>
                      )}
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
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
                      {hasData && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0"
                          onClick={() => toggleDim(dim.key)}
                        >
                          {isExpanded ? (
                            <ChevronUp className="h-3.5 w-3.5" />
                          ) : (
                            <ChevronDown className="h-3.5 w-3.5" />
                          )}
                        </Button>
                      )}
                    </div>
                  </div>
                </CardHeader>
                {isExpanded && hasData && (
                  <CardContent>
                    <AnalysisDimView dimension={dim.key} data={dimData} />
                  </CardContent>
                )}
                {!hasData && (
                  <CardContent>
                    <p className="text-xs text-muted-foreground">
                      {t("analysis.clickToRun")}
                    </p>
                  </CardContent>
                )}
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
