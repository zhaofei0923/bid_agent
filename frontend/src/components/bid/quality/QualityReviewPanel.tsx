"use client"

import { memo, useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { qualityReviewService } from "@/services/quality-review"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { QualityReviewResult } from "@/types/generation"
import { useTranslations } from "next-intl"

interface QualityReviewPanelProps {
  projectId: string
}

export const QualityReviewPanel = memo(function QualityReviewPanel({
  projectId,
}: QualityReviewPanelProps) {
  const { completeStep, goToStep } = useBidWorkspaceStore()
  const t = useTranslations("bid")
  const [reviewResult, setReviewResult] = useState<QualityReviewResult | null>(
    null
  )
  const [proposalContent, setProposalContent] = useState("")

  const fullReviewMutation = useMutation({
    mutationFn: (content: string) =>
      qualityReviewService.fullReview(projectId, content),
    onSuccess: (data) => setReviewResult(data),
  })

  const quickReviewMutation = useMutation({
    mutationFn: (content: string) =>
      qualityReviewService.quickReview(projectId, content),
    onSuccess: (data) => setReviewResult(data),
  })

  const handleNext = () => {
    completeStep("review")
  }

  const severityColors: Record<string, string> = {
    high: "bg-red-100 text-red-800",
    medium: "bg-yellow-100 text-yellow-800",
    low: "bg-blue-100 text-blue-800",
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">{t("quality.title")}</h2>
        <p className="text-muted-foreground text-sm mt-1">
          {t("quality.subtitle")}
        </p>
      </div>

      {/* Input */}
      <Card>
        <CardHeader className="pb-2">
          <h3 className="text-sm font-semibold">{t("quality.proposalContent")}</h3>
        </CardHeader>
        <CardContent>
          <textarea
            value={proposalContent}
            onChange={(e) => setProposalContent(e.target.value)}
            placeholder={t("quality.placeholder")}
            className="w-full min-h-[200px] rounded-md border border-input bg-background p-3 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
          <div className="mt-3 flex gap-2">
            <Button
              onClick={() => fullReviewMutation.mutate(proposalContent)}
              disabled={
                !proposalContent.trim() || fullReviewMutation.isPending
              }
            >
              {fullReviewMutation.isPending ? t("quality.reviewing") : t("quality.fullReview")}
            </Button>
            <Button
              variant="outline"
              onClick={() => quickReviewMutation.mutate(proposalContent)}
              disabled={
                !proposalContent.trim() || quickReviewMutation.isPending
              }
            >
              {quickReviewMutation.isPending ? t("quality.checking") : t("quality.quickReview")}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {reviewResult && (
        <>
          {/* Overall score */}
          <Card>
            <CardContent className="py-6 text-center">
              <div className="text-4xl font-bold text-primary mb-1">
                {reviewResult.overall_score}
              </div>
              <p className="text-sm text-muted-foreground">{t("quality.overallScore")} {t("quality.outOf100")}</p>
            </CardContent>
          </Card>

          {/* Dimensions */}
          <div className="grid grid-cols-2 gap-4">
            {reviewResult.dimensions.map((dim) => (
              <Card key={dim.name}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold">{dim.name}</h3>
                    <span className="text-sm font-bold text-primary">
                      {dim.score}/{dim.max_score}
                    </span>
                  </div>
                </CardHeader>
                <CardContent>
                  {dim.findings.length > 0 && (
                    <div className="mb-2">
                      <p className="text-xs font-medium text-muted-foreground mb-1">
                        {t("quality.findings")}
                      </p>
                      <ul className="text-xs space-y-1">
                        {dim.findings.map((f, i) => (
                          <li key={i}>· {f}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {dim.suggestions.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-muted-foreground mb-1">
                        {t("quality.suggestions")}
                      </p>
                      <ul className="text-xs space-y-1">
                        {dim.suggestions.map((s, i) => (
                          <li key={i}>💡 {s}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Risk items */}
          {reviewResult.risk_items.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <h3 className="text-sm font-semibold">{t("quality.riskItems")}</h3>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {reviewResult.risk_items.map((risk, i) => (
                    <div key={i} className="border-b last:border-0 pb-3">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge
                          variant="secondary"
                          className={severityColors[risk.severity] || ""}
                        >
                          {risk.severity === "high"
                            ? t("quality.highRisk")
                            : risk.severity === "medium"
                              ? t("quality.mediumRisk")
                              : t("quality.lowRisk")}
                        </Badge>
                      </div>
                      <p className="text-sm">{risk.description}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {t("quality.recommendation", { text: risk.recommendation })}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {reviewResult && (
        <div className="flex justify-end">
          <Button onClick={handleNext}>{t("quality.nextStep")}</Button>
        </div>
      )}
    </div>
  )
})
