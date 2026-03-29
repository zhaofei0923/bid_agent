"use client"

import { memo, useRef, useState } from "react"
import { useMutation, useQuery } from "@tanstack/react-query"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { checklistService } from "@/services/bid-analysis"
import { documentReviewService } from "@/services/document-review"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { useTranslations } from "next-intl"
import type { ChecklistItem, ChecklistSection, DocumentReviewResult } from "@/types/bid"

interface DocumentReviewPanelProps {
  projectId: string
}

// ── Score badge ──────────────────────────────────────────────────

function ScoreBadge({ score, meets }: { score: number; meets: boolean }) {
  const color = meets
    ? "bg-green-100 text-green-700 border-green-200"
    : score >= 50
    ? "bg-yellow-100 text-yellow-700 border-yellow-200"
    : "bg-red-100 text-red-700 border-red-200"
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-sm font-semibold ${color}`}
    >
      {score}分
    </span>
  )
}

// ── Review result card ──────────────────────────────────────────

function ReviewResultCard({
  result,
  t,
}: {
  result: DocumentReviewResult
  t: ReturnType<typeof useTranslations>
}) {
  return (
    <div className="mt-3 space-y-3 rounded-xl border border-stone-200 bg-white p-4">
      {/* Score row */}
      <div className="flex items-center gap-3">
        <ScoreBadge score={result.score} meets={result.meets_requirements} />
        <span className="text-sm font-medium text-slate-600">
          {result.meets_requirements
            ? t("documentReview.meetsRequirements")
            : t("documentReview.notMeetsRequirements")}
        </span>
      </div>

      {/* Gaps */}
      {result.gaps.length > 0 && (
        <div>
          <p className="mb-1.5 text-[11px] font-semibold text-red-600">
            ⚠ {t("documentReview.gaps")}
          </p>
          <ul className="space-y-1">
            {result.gaps.map((gap, i) => (
              <li key={i} className="text-sm text-slate-700 flex gap-1.5">
                <span className="mt-0.5 shrink-0 text-red-400">•</span>
                {gap}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Suggestions */}
      {result.suggestions.length > 0 && (
        <div>
          <p className="mb-1.5 text-[11px] font-semibold text-blue-600">
            💡 {t("documentReview.suggestions")}
          </p>
          <ul className="space-y-1">
            {result.suggestions.map((s, i) => (
              <li key={i} className="text-sm text-slate-700 flex gap-1.5">
                <span className="mt-0.5 shrink-0 text-blue-400">•</span>
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Knowledge tips */}
      {result.knowledge_tips.length > 0 && (
        <div className="rounded-lg border border-indigo-100 bg-indigo-50 px-3 py-2.5">
          <p className="mb-1.5 text-[11px] font-semibold text-indigo-600">
            📚 {t("documentReview.knowledgeTips")}
          </p>
          <ul className="space-y-1">
            {result.knowledge_tips.map((tip, i) => (
              <li key={i} className="text-xs text-indigo-800 flex gap-1.5">
                <span className="mt-0.5 shrink-0">•</span>
                {tip}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

// ── Item row with inline review ──────────────────────────────────

function ReviewItemRow({
  item,
  index,
  projectId,
  t,
}: {
  item: ChecklistItem
  index: number
  projectId: string
  t: ReturnType<typeof useTranslations>
}) {
  const [open, setOpen] = useState(false)
  const [tab, setTab] = useState<"text" | "file">("text")
  const [textContent, setTextContent] = useState("")
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [result, setResult] = useState<DocumentReviewResult | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const reviewMutation = useMutation({
    mutationFn: () =>
      documentReviewService.reviewItem(projectId, {
        item_title: item.title,
        item_guidance: item.guidance ?? undefined,
        source_section: item.source?.section_title ?? undefined,
        source_excerpt: item.source?.excerpt ?? undefined,
        content_text: tab === "text" ? textContent : undefined,
        file: tab === "file" && selectedFile ? selectedFile : undefined,
      }),
    onSuccess: (data) => {
      if (data.success && data.data) {
        setResult(data.data)
      }
    },
  })

  const canReview =
    tab === "text" ? textContent.trim().length > 0 : selectedFile !== null

  return (
    <div className="border-b border-stone-100 last:border-0">
      {/* Header row */}
      <button
        className="flex w-full items-start gap-3 px-4 py-3 text-left hover:bg-stone-50 transition-colors"
        onClick={() => setOpen((v) => !v)}
      >
        <span className="mt-0.5 w-5 shrink-0 text-center text-xs font-semibold text-stone-400">
          {index + 1}
        </span>
        <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2">
          <span className="font-medium text-sm text-slate-800">{item.title}</span>
          {item.required ? (
            <Badge className="h-4 shrink-0 bg-red-100 px-1.5 text-[10px] text-red-700 hover:bg-red-100">
              必填
            </Badge>
          ) : (
            <Badge
              variant="secondary"
              className="h-4 shrink-0 px-1.5 text-[10px] text-stone-500"
            >
              选填
            </Badge>
          )}
          {result && (
            <ScoreBadge score={result.score} meets={result.meets_requirements} />
          )}
        </div>
        <span className="ml-2 shrink-0 text-stone-400 text-xs mt-0.5">
          {open ? "▲" : "▼"}
        </span>
      </button>

      {/* Expanded review area */}
      {open && (
        <div className="bg-stone-50 px-4 pb-4 pt-2 space-y-3">
          {/* Guidance context */}
          {item.guidance && (
            <div className="rounded-lg border border-blue-100 bg-blue-50 px-3 py-2.5">
              <p className="mb-1 text-[11px] font-semibold text-blue-600">
                📝 编写指导
              </p>
              <p className="text-sm leading-relaxed text-slate-700">
                {item.guidance}
              </p>
            </div>
          )}

          {/* Tab switcher */}
          <div className="flex gap-2">
            <button
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                tab === "text"
                  ? "bg-slate-800 text-white"
                  : "bg-white border border-stone-200 text-slate-600 hover:bg-stone-50"
              }`}
              onClick={() => setTab("text")}
            >
              {t("documentReview.tabText")}
            </button>
            <button
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                tab === "file"
                  ? "bg-slate-800 text-white"
                  : "bg-white border border-stone-200 text-slate-600 hover:bg-stone-50"
              }`}
              onClick={() => setTab("file")}
            >
              {t("documentReview.tabFile")}
            </button>
          </div>

          {/* Input area */}
          {tab === "text" ? (
            <Textarea
              value={textContent}
              onChange={(e) => setTextContent(e.target.value)}
              placeholder={t("documentReview.textPlaceholder")}
              className="min-h-[100px] resize-none text-sm"
            />
          ) : (
            <div
              className="flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-stone-300 bg-white px-4 py-6 text-center cursor-pointer hover:border-stone-400 transition-colors"
              onClick={() => fileInputRef.current?.click()}
            >
              {selectedFile ? (
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-slate-700">
                    📎 {selectedFile.name}
                  </span>
                  <button
                    className="text-xs text-red-500 hover:text-red-700"
                    onClick={(e) => {
                      e.stopPropagation()
                      setSelectedFile(null)
                    }}
                  >
                    ✕
                  </button>
                </div>
              ) : (
                <>
                  <span className="text-2xl">📄</span>
                  <p className="text-sm text-slate-600">
                    {t("documentReview.uploadHint")}
                  </p>
                </>
              )}
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept=".pdf,.jpg,.jpeg,.png,.webp"
                onChange={(e) => {
                  const f = e.target.files?.[0] ?? null
                  setSelectedFile(f)
                  e.target.value = ""
                }}
              />
            </div>
          )}

          {/* Review button */}
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              disabled={!canReview || reviewMutation.isPending}
              onClick={() => reviewMutation.mutate()}
              className="text-xs"
            >
              {reviewMutation.isPending ? (
                <>
                  <span className="mr-1.5 h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  {t("documentReview.reviewing")}
                </>
              ) : (
                `🔍 ${t("documentReview.reviewBtn")}`
              )}
            </Button>
            {reviewMutation.isError && (
              <span className="text-xs text-red-500">审查失败，请重试</span>
            )}
          </div>

          {/* Result */}
          {result && <ReviewResultCard result={result} t={t} />}
        </div>
      )}
    </div>
  )
}

// ── Section block ────────────────────────────────────────────────

function ReviewSectionBlock({
  section,
  projectId,
  t,
}: {
  section: ChecklistSection
  projectId: string
  t: ReturnType<typeof useTranslations>
}) {
  const [open, setOpen] = useState(true)

  return (
    <div className="rounded-xl border border-stone-200 overflow-hidden">
      <button
        className="flex w-full items-center gap-3 bg-slate-50 px-4 py-3 text-left hover:bg-slate-100 transition-colors"
        onClick={() => setOpen((v) => !v)}
      >
        <span className="text-lg">{section.icon}</span>
        <span className="flex-1 font-semibold text-slate-800">{section.title}</span>
        <Badge variant="secondary" className="text-xs">
          {section.items.length} 项
        </Badge>
        <span className="ml-1 text-stone-400 text-xs">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="divide-y divide-stone-100">
          {section.items.map((item, i) => (
            <ReviewItemRow
              key={item.id}
              item={item}
              index={i}
              projectId={projectId}
              t={t}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────

export const DocumentReviewPanel = memo(function DocumentReviewPanel({
  projectId,
}: DocumentReviewPanelProps) {
  const { completeStep, goToStep } = useBidWorkspaceStore()
  const t = useTranslations("bid")

  const handleNext = () => {
    completeStep("review")
    goToStep("tracking")
  }

  // Read checklist from cache (no force-regenerate)
  const { data: checklist, isLoading } = useQuery({
    queryKey: ["checklist", projectId],
    queryFn: () => checklistService.generate(projectId, false),
    retry: false,
  })

  const hasSections = checklist && checklist.sections.length > 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold">{t("documentReview.title")}</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          {t("documentReview.subtitle")}
        </p>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-16 animate-pulse rounded-xl bg-stone-100"
            />
          ))}
        </div>
      )}

      {/* No checklist yet */}
      {!isLoading && !hasSections && (
        <div className="rounded-xl border border-dashed border-stone-300 py-12 text-center">
          <p className="text-slate-500 text-sm">{t("documentReview.noChecklist")}</p>
          <Button
            variant="outline"
            size="sm"
            className="mt-4 text-xs"
            onClick={() => goToStep("writing")}
          >
            {t("documentReview.goToChecklist")}
          </Button>
        </div>
      )}

      {/* Checklist sections */}
      {hasSections && (
        <div className="space-y-4">
          {checklist.sections.map((section) => (
            <ReviewSectionBlock
              key={section.id}
              section={section}
              projectId={projectId}
              t={t}
            />
          ))}
        </div>
      )}

      {/* Next step button */}
      {hasSections && (
        <div className="flex justify-end">
          <Button size="sm" onClick={handleNext}>
            {t("documentReview.nextStep")}
          </Button>
        </div>
      )}
    </div>
  )
})
