"use client"

import { memo, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { checklistService } from "@/services/bid-analysis"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useTranslations } from "next-intl"
import type { ChecklistItem, ChecklistSection } from "@/types/bid"

interface ChecklistStepProps {
  projectId: string
}

// ── Item row (collapsible) ────────────────────────────────────────

function ItemRow({
  item,
  index,
}: {
  item: ChecklistItem
  index: number
}) {
  const [open, setOpen] = useState(false)

  return (
    <div className="border-b border-stone-100 last:border-0">
      {/* Header row — always visible */}
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
          {item.form_reference && (
            <Badge className="h-4 shrink-0 bg-indigo-100 px-1.5 text-[10px] text-indigo-700 hover:bg-indigo-100">
              {item.form_reference}
            </Badge>
          )}
          {item.copies != null && (
            <span className="text-[11px] text-stone-400">{item.copies} 份</span>
          )}
          {item.format_hint && (
            <span className="text-[11px] text-stone-400 italic">{item.format_hint}</span>
          )}
        </div>
        <span className="ml-2 shrink-0 text-stone-400 text-xs mt-0.5">
          {open ? "▲" : "▼"}
        </span>
      </button>

      {/* Expanded detail */}
      {open && (
        <div className="bg-stone-50 px-4 pb-4 pt-1 space-y-3">
          {/* Guidance */}
          {item.guidance && (
            <div className="rounded-lg border border-blue-100 bg-blue-50 px-3 py-2.5">
              <p className="mb-1 text-[11px] font-semibold text-blue-600">📝 编写指导</p>
              <p className="text-sm leading-relaxed text-slate-700">{item.guidance}</p>
            </div>
          )}

          {/* Source */}
          {(item.source?.section_title || item.source?.excerpt) && (
            <div className="rounded-lg border border-stone-200 bg-white px-3 py-2.5">
              <p className="mb-1.5 text-[11px] font-semibold text-stone-500">
                📄 招标文件出处
              </p>
              <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-stone-500">
                {item.source.filename && (
                  <span className="rounded bg-stone-100 px-1.5 py-0.5">
                    {item.source.filename}
                  </span>
                )}
                {item.source.page_number != null && (
                  <span className="rounded bg-stone-100 px-1.5 py-0.5">
                    第 {item.source.page_number} 页
                  </span>
                )}
                {item.source.section_title && (
                  <span className="rounded bg-stone-100 px-1.5 py-0.5">
                    {item.source.section_title}
                  </span>
                )}
              </div>
              {item.source.excerpt && (
                <p className="mt-2 text-xs italic leading-relaxed text-stone-500 border-l-2 border-stone-300 pl-2">
                  {item.source.excerpt}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Section block (collapsible) ───────────────────────────────────

function SectionBlock({
  section,
  defaultOpen,
}: {
  section: ChecklistSection
  defaultOpen: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <div className="rounded-xl border border-stone-200 overflow-hidden">
      {/* Section header */}
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

      {/* Items */}
      {open && (
        <div className="divide-y divide-stone-100">
          {section.items.map((item, i) => (
            <ItemRow key={item.id} item={item} index={i} />
          ))}
        </div>
      )}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────

export const ChecklistStep = memo(function ChecklistStep({
  projectId,
}: ChecklistStepProps) {
  const { completeStep, goToStep } = useBidWorkspaceStore()
  const t = useTranslations("bid")
  const queryClient = useQueryClient()
  const [allOpen, setAllOpen] = useState(true)

  const handleNext = () => {
    completeStep("writing")
    goToStep("review")
  }

  // ── Query: load cached checklist on mount (use cache, no force) ──
  const { data: cachedData, isLoading } = useQuery({
    queryKey: ["checklist", projectId],
    queryFn: () => checklistService.generate(projectId, false),
    retry: false,
  })

  // ── Mutation: (re)generate ──
  const generateMutation = useMutation({
    mutationFn: (force: boolean) => checklistService.generate(projectId, force),
    onSuccess: (data) => {
      queryClient.setQueryData(["checklist", projectId], data)
    },
  })

  const checklist = generateMutation.data ?? cachedData
  const isGenerating = generateMutation.isPending

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">{t("checklist.title")}</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {t("checklist.subtitle")}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {checklist && (
            <>
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-stone-500"
                onClick={() => setAllOpen((v) => !v)}
              >
                {allOpen ? "折叠全部" : "展开全部"}
              </Button>
              {checklist.cached && (
                <Badge
                  variant="secondary"
                  className="text-[10px] text-stone-400"
                >
                  已缓存
                </Badge>
              )}
            </>
          )}
          <Button
            onClick={() => generateMutation.mutate(true)}
            disabled={isGenerating}
            size="sm"
          >
            {isGenerating ? (
              <>
                <span className="mr-2 h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                {t("checklist.generating")}
              </>
            ) : checklist ? (
              t("checklist.regenerate")
            ) : (
              t("checklist.generate")
            )}
          </Button>
        </div>
      </div>

      {/* ── Loading skeleton ── */}
      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((n) => (
            <Skeleton key={n} className="h-14 w-full rounded-xl" />
          ))}
        </div>
      )}

      {/* ── Generating animation ── */}
      {isGenerating && (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((n) => (
            <Skeleton key={n} className="h-14 w-full animate-pulse rounded-xl" />
          ))}
        </div>
      )}

      {/* ── Empty state ── */}
      {!isLoading && !isGenerating && !checklist && (
        <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-stone-200 py-16 text-center">
          <p className="text-4xl mb-4">📋</p>
          <p className="font-medium text-slate-700">{t("checklist.title")}</p>
          <p className="mt-1 text-sm text-muted-foreground max-w-sm">
            {t("checklist.empty")}
          </p>
          <Button
            className="mt-6"
            onClick={() => generateMutation.mutate(true)}
          >
            ✨ {t("checklist.generate")}
          </Button>
        </div>
      )}

      {/* ── Checklist sections ── */}
      {!isGenerating && checklist && checklist.sections.length > 0 && (
        <div className="space-y-3">
          {checklist.sections.map((section, i) => (
            <SectionBlock
              key={section.id || i}
              section={section}
              defaultOpen={allOpen}
            />
          ))}
        </div>
      )}

      {/* ── Error state ── */}
      {generateMutation.isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          生成失败，请稍后重试
        </div>
      )}

      {/* ── Next step ── */}
      {checklist && checklist.sections.length > 0 && (
        <div className="flex justify-end">
          <Button onClick={handleNext}>{t("checklist.nextStep")}</Button>
        </div>
      )}
    </div>
  )
})
