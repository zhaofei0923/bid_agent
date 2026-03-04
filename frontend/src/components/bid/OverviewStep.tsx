"use client"

import { memo, useState } from "react"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { useDocuments, useDocumentSections } from "@/hooks/use-documents"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useTranslations } from "next-intl"
import type { ProjectDocument, DocumentSection } from "@/types"

// ──────────────────────────────────────────────
// Section type → color mapping
// ──────────────────────────────────────────────
const SECTION_TYPE_COLOR: Record<string, string> = {
  tor: "bg-indigo-100 text-indigo-700 border-indigo-200",
  references_to_tor: "bg-indigo-100 text-indigo-700 border-indigo-200",
  qualification: "bg-amber-100 text-amber-700 border-amber-200",
  qualification_requirements: "bg-amber-100 text-amber-700 border-amber-200",
  evaluation: "bg-emerald-100 text-emerald-700 border-emerald-200",
  evaluation_criteria: "bg-emerald-100 text-emerald-700 border-emerald-200",
  key_dates: "bg-purple-100 text-purple-700 border-purple-200",
  timeline: "bg-purple-100 text-purple-700 border-purple-200",
  submission: "bg-yellow-100 text-yellow-700 border-yellow-200",
  submission_requirements: "bg-yellow-100 text-yellow-700 border-yellow-200",
  commercial: "bg-teal-100 text-teal-700 border-teal-200",
  technical: "bg-sky-100 text-sky-700 border-sky-200",
}
const DEFAULT_SECTION_COLOR = "bg-stone-100 text-stone-600 border-stone-200"

function getSectionColor(type: string) {
  return SECTION_TYPE_COLOR[type.toLowerCase()] ?? DEFAULT_SECTION_COLOR
}

// ──────────────────────────────────────────────
// Sub-components
// ──────────────────────────────────────────────

function DocStatusBadge({ status }: { status: string }) {
  const t = useTranslations("bid")
  const map: Record<string, string> = {
    completed: "bg-emerald-100 text-emerald-700 border-emerald-200",
    processing: "bg-blue-100 text-blue-700 border-blue-200",
    pending: "bg-stone-100 text-stone-600 border-stone-200",
    failed: "bg-red-100 text-red-700 border-red-200",
  }
  const cls = map[status] ?? map.pending
  const label =
    status === "completed"
      ? t("overview.completed")
      : status === "processing" || status === "pending"
        ? t("overview.processing")
        : t("overview.failed")
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${cls}`}
    >
      {label}
    </span>
  )
}

function DocMetaCard({ doc }: { doc: ProjectDocument }) {
  const t = useTranslations("bid")
  const ext = (doc.original_filename || doc.filename).split(".").pop()?.toUpperCase() ?? ""
  const sizeKb = doc.file_size != null ? Math.round(doc.file_size / 1024) : null
  const isProcessing = doc.status === "processing" || doc.status === "pending"

  return (
    <div className="flex items-center gap-4 rounded-xl border border-stone-200 bg-white px-4 py-3 shadow-sm">
      {/* File icon */}
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-stone-100 text-lg">
        📄
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-slate-900">
          {doc.original_filename || doc.filename}
        </p>
        <p className="mt-0.5 text-xs text-muted-foreground">
          {ext}
          {sizeKb != null && ` · ${sizeKb} KB`}
          {doc.page_count != null && ` · ${doc.page_count} ${t("overview.pages")}`}
          {doc.detected_institution && ` · ${doc.detected_institution.toUpperCase()}`}
        </p>
        {isProcessing && (
          <div className="mt-2">
            <Progress value={doc.processing_progress} className="h-1.5" />
            <p className="mt-1 text-xs text-blue-600">{t("overview.processingHint")}</p>
          </div>
        )}
      </div>
      <DocStatusBadge status={doc.status} />
    </div>
  )
}

function SectionRow({ section }: { section: DocumentSection }) {
  const [open, setOpen] = useState(false)
  const colorCls = getSectionColor(section.section_type)
  const detail = section.ai_summary || section.content_preview

  return (
    <div className="rounded-lg border border-stone-100 bg-white">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-stone-50"
      >
        {/* Section type badge */}
        <span
          className={`inline-flex shrink-0 items-center rounded-full border px-2 py-0.5 text-xs font-medium ${colorCls}`}
        >
          {section.section_type}
        </span>

        {/* Title */}
        <span className="flex-1 truncate text-sm font-medium text-slate-800">
          {section.section_number && (
            <span className="mr-1.5 text-muted-foreground">{section.section_number}</span>
          )}
          {section.section_title ?? section.section_type}
        </span>

        {/* Page range */}
        <span className="shrink-0 rounded-md bg-stone-100 px-2 py-0.5 text-xs text-muted-foreground">
          P{section.start_page}–P{section.end_page}
        </span>

        {/* Chevron */}
        {detail && (
          <span
            className={`shrink-0 text-muted-foreground transition-transform ${open ? "rotate-90" : ""}`}
          >
            ›
          </span>
        )}
      </button>

      {open && detail && (
        <div className="border-t border-stone-100 px-4 py-3">
          <p className="whitespace-pre-line text-sm leading-relaxed text-slate-700">{detail}</p>
          {section.reading_guide && (
            <p className="mt-2 text-xs italic text-muted-foreground">{section.reading_guide}</p>
          )}
        </div>
      )}
    </div>
  )
}

function DocDetailPanel({
  projectId,
  doc,
}: {
  projectId: string
  doc: ProjectDocument
}) {
  const t = useTranslations("bid")
  const isProcessing = doc.status === "processing" || doc.status === "pending"
  const { data: sections, isLoading: sectionsLoading } = useDocumentSections(
    projectId,
    doc.id
  )

  return (
    <div className="space-y-5">
      {/* Block B: AI Interpretation */}
      <Card>
        <CardHeader className="pb-2">
          <h3 className="text-sm font-semibold">{t("overview.aiReading")}</h3>
        </CardHeader>
        <CardContent className="space-y-4">
          {isProcessing ? (
            <div className="space-y-2">
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

      {/* Block C: Section Structure Tree */}
      <Card>
        <CardHeader className="pb-2">
          <h3 className="text-sm font-semibold">{t("overview.sectionStructure")}</h3>
        </CardHeader>
        <CardContent>
          {isProcessing || sectionsLoading ? (
            <div className="space-y-2">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-12 w-full rounded-lg" />
              ))}
            </div>
          ) : sections && sections.length > 0 ? (
            <div className="space-y-2">
              {sections.map((s) => (
                <SectionRow key={s.id} section={s} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">{t("overview.noSections")}</p>
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
      {/* Block A: Document meta cards */}
      <div className="space-y-2">
        {documents.map((doc) => (
          <DocMetaCard key={doc.id} doc={doc} />
        ))}
      </div>

      {/* Blocks B + C: per-document detail, with Tabs if multiple docs */}
      {documents.length === 1 ? (
        <DocDetailPanel projectId={projectId} doc={documents[0]} />
      ) : (
        <Tabs defaultValue={documents[0].id}>
          <TabsList className="mb-4">
            {documents.map((doc, i) => (
              <TabsTrigger key={doc.id} value={doc.id} className="max-w-[200px] truncate">
                {doc.original_filename || doc.filename || `Vol ${i + 1}`}
              </TabsTrigger>
            ))}
          </TabsList>
          {documents.map((doc) => (
            <TabsContent key={doc.id} value={doc.id}>
              <DocDetailPanel projectId={projectId} doc={doc} />
            </TabsContent>
          ))}
        </Tabs>
      )}

      <div className="flex justify-end pt-2">
        <Button onClick={handleNext}>{t("overview.nextStep")}</Button>
      </div>
    </div>
  )
})
