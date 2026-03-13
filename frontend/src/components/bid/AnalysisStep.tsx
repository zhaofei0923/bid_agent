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
  executive_summary: "executive_summary",
  qualification: "qualification_requirements",
  evaluation: "evaluation_criteria",
  key_dates: "key_dates",
  submission: "submission_checklist",
  bds_analysis: "bds_modifications",
  technical_requirements: "technical_requirements",
  methodology: "evaluation_methodology",
  technical_strategy: "technical_strategy",
  compliance_matrix: "compliance_matrix",
}

const ANALYSIS_DIMENSIONS = [
  { key: "executive_summary", icon: "🏢" },
  { key: "key_dates", icon: "📅" },
  { key: "qualification", icon: "📋" },
  { key: "evaluation", icon: "📊" },
  { key: "submission", icon: "📦" },
  { key: "bds_analysis", icon: "📝" },
  { key: "technical_requirements", icon: "🔧" },
  { key: "methodology", icon: "📐" },
  { key: "technical_strategy", icon: "🎯" },
  { key: "compliance_matrix", icon: "✅" },
] as const

// One-line summary shown in collapsed header
function getDimSummary(key: string, data: Record<string, unknown>): string {
  const a = (v: unknown) => (Array.isArray(v) ? v : [])
  const r = (v: unknown): Record<string, unknown> =>
    v && typeof v === "object" && !Array.isArray(v) ? (v as Record<string, unknown>) : {}
  const n = (v: unknown) => (typeof v === "number" ? v : 0)
  const s = (v: unknown) => (typeof v === "string" ? v : "")
  switch (key) {
    case "executive_summary": {
      const scope = s(data.project_scope_summary)
      const method = r(data.procurement_method)
      return scope || s(method.type) || ""
    }
    case "qualification":
      return `${a(data.qualification_requirements).length} 类资质要求`
    case "evaluation": {
      const em = r(data.evaluation_method)
      const tw = n(data.technical_weight)
      const m = s(em.type) || s(data.evaluation_method)
      return m ? `${m} · 技术权重 ${tw}%` : tw > 0 ? `技术权重 ${tw}%` : ""
    }
    case "key_dates": {
      const d = a(data.key_dates)
      const urgency = r(data.urgency_assessment)
      const level = s(urgency.level)
      const urgencyLabel = level === "red" ? "🔴 紧急" : level === "yellow" ? "🟡 注意" : level === "green" ? "🟢 充裕" : ""
      return `${d.length} 个关键日期${urgencyLabel ? ` · ${urgencyLabel}` : ""}`
    }
    case "bds_analysis": {
      const mods = a(data.bds_modifications)
      const stats = r(data.statistics)
      const critical = n(stats.critical_count)
      const high = n(stats.high_count)
      const hi = critical + high || mods.filter(
        (m) =>
          typeof m === "object" &&
          m !== null &&
          ["critical", "high"].includes(s((m as Record<string, unknown>).priority)),
      ).length
      return `${mods.length} 条修改${hi > 0 ? `，${hi} 条高优先级` : ""}`
    }
    case "technical_requirements": {
      const deliverables = a(data.deliverables)
      const personnel = a(data.key_personnel)
      const parts = []
      if (deliverables.length > 0) parts.push(`${deliverables.length} 项交付物`)
      if (personnel.length > 0) parts.push(`${personnel.length} 个关键岗位`)
      return parts.join(" · ") || ""
    }
    case "methodology": {
      const method = s(data.evaluation_approach) || s(data.method_type)
      return method || ""
    }
    case "technical_strategy": {
      const strengths = a(data.strengths || data.competitive_advantages)
      const weaknesses = a(data.weaknesses || data.gaps)
      const parts: string[] = []
      if (strengths.length > 0) parts.push(`${strengths.length} 项优势`)
      if (weaknesses.length > 0) parts.push(`${weaknesses.length} 项短板`)
      return parts.join(" · ") || ""
    }
    case "compliance_matrix": {
      const summary = r(data.summary)
      const mandatory = n(summary.total_mandatory)
      const risk = s(summary.overall_compliance_risk)
      const riskLabel = risk === "high" ? "🔴 高风险" : risk === "medium" ? "🟡 中风险" : risk === "low" ? "🟢 低风险" : ""
      return mandatory > 0 ? `${mandatory} 项强制要求${riskLabel ? ` · ${riskLabel}` : ""}` : ""
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
          {/* ── Risk Assessment — collapsible card at top ── */}
          {(() => {
            const riskData = analysis.risk_assessment as Record<
              string,
              unknown
            > | null
            const hasData = riskData && Object.keys(riskData).length > 0
            const isExpanded = expandedDims.has("risk_assessment")
            return (
              <Card
                className={hasData ? "cursor-pointer transition-colors hover:bg-slate-50" : ""}
                onClick={hasData ? () => toggleDim("risk_assessment") : undefined}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span>⚠️</span>
                      <h3 className="text-sm font-semibold">
                        {t("analysis.dimensions.risk_assessment")}
                      </h3>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      <Badge variant={hasData ? "default" : "secondary"}>
                        {hasData ? t("analysis.completed") : t("analysis.pending")}
                      </Badge>
                      {hasData && (
                        <span className="text-muted-foreground">
                          {isExpanded ? (
                            <ChevronUp className="h-4 w-4" />
                          ) : (
                            <ChevronDown className="h-4 w-4" />
                          )}
                        </span>
                      )}
                    </div>
                  </div>
                  {hasData && !isExpanded && (
                    <p className="mt-1 text-xs text-muted-foreground/60">
                      点击展开详情 →
                    </p>
                  )}
                </CardHeader>
                {isExpanded && hasData && (
                  <CardContent>
                    <AnalysisDimView dimension="risk_assessment" data={riskData} />
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
          })()}

          {/* ── Other dimensions — full-width stacked, accordion ── */}
          {ANALYSIS_DIMENSIONS.map((dim) => {
            const field = FIELD_MAP[dim.key]
            const dimData = analysis[field] as Record<string, unknown> | null
            const hasData = dimData && Object.keys(dimData).length > 0
            const isExpanded = expandedDims.has(dim.key)
            const summary = hasData ? getDimSummary(dim.key, dimData) : ""

            return (
              <Card
                key={dim.key}
                className={hasData ? "cursor-pointer transition-colors hover:bg-slate-50" : ""}
                onClick={hasData ? () => toggleDim(dim.key) : undefined}
              >
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
                      {hasData && (
                        <span className="text-muted-foreground">
                          {isExpanded ? (
                            <ChevronUp className="h-4 w-4" />
                          ) : (
                            <ChevronDown className="h-4 w-4" />
                          )}
                        </span>
                      )}
                    </div>
                  </div>
                  {hasData && !isExpanded && (
                    <p className="mt-1 text-xs text-muted-foreground/60">
                      点击展开详情 →
                    </p>
                  )}
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

      {analysis && (() => {
        const dims = ANALYSIS_DIMENSIONS.map((d) => FIELD_MAP[d.key])
        const completedCount = dims.filter(
          (f) => {
            const v = analysis[f] as Record<string, unknown> | null
            return v && Object.keys(v).length > 0
          }
        ).length
        return completedCount > 0 ? (
          <div className="flex justify-end">
            <Button onClick={handleNext}>{t("analysis.nextStep")}</Button>
          </div>
        ) : null
      })()}
    </div>
  )
})
