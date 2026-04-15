"use client"

import { use, useEffect, useRef, useState } from "react"
import { useTranslations } from "next-intl"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { projectService } from "@/services/projects"
import { documentService } from "@/services/documents"
import { bidPlanService } from "@/services/bid-plan"
import { checklistService } from "@/services/bid-analysis"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { BidProgressNav } from "@/components/bid/BidProgressNav"
import { BidWorkspace } from "@/components/bid/BidWorkspace"
import { BidChatPanel } from "@/components/bid/BidChatPanel"
import { Button } from "@/components/ui/button"
import type { BidStep } from "@/types"

type AutoGenStatus = "idle" | "running" | "done" | "error"

export default function WorkspacePage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const t = useTranslations("workspace")
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"
  const { setProject, initSteps, isChatPanelOpen, toggleChatPanel, chatMode, goToStep } =
    useBidWorkspaceStore()
  const initRef = useRef<string | null>(null)
  const autoGenRef = useRef(false)
  const queryClient = useQueryClient()

  const [autoGenStatus, setAutoGenStatus] = useState<AutoGenStatus>("idle")
  const [autoGenBannerVisible, setAutoGenBannerVisible] = useState(false)

  const { data: project } = useQuery({
    queryKey: ["project", id],
    queryFn: () => projectService.getById(id),
  })

  const { data: documents, isFetched: docsFetched } = useQuery({
    queryKey: ["documents", id],
    queryFn: () => documentService.list(id),
    enabled: !!id,
  })

  const { data: plan, isFetched: planFetched } = useQuery({
    queryKey: ["bid-plan", id],
    queryFn: () => bidPlanService.getByProject(id),
    enabled: !!id,
    retry: false,
  })

  // Immediately reset store when project id changes
  useEffect(() => {
    setProject(id, project?.institution || "adb")
  }, [id, setProject]) // eslint-disable-line react-hooks/exhaustive-deps

  // Update institution when project loads
  useEffect(() => {
    if (project?.institution) {
      setProject(id, project.institution)
    }
  }, [id, project, setProject])

  // Auto-detect completed steps from backend data
  useEffect(() => {
    // Only run once per project id when all queries have settled
    if (initRef.current === id) return
    if (!docsFetched || !planFetched) return

    const SUCCESS = new Set(["processed", "completed"])
    const hasProcessedDocs =
      !!documents && documents.length > 0 && documents.every((d) => SUCCESS.has(d.status))
    const hasOverview = !!project?.combined_ai_overview
    const hasPlan = !!plan

    const completed: BidStep[] = []
    let current: BidStep = "upload"

    if (hasProcessedDocs) {
      completed.push("upload")
      current = "overview"
    }
    if (hasOverview) {
      if (!completed.includes("upload")) completed.push("upload")
      completed.push("overview")
      current = "plan"
    }
    if (hasPlan) {
      if (!completed.includes("overview")) {
        completed.push("upload", "overview")
      }
      completed.push("plan", "writing")
      current = "writing"
    }

    // Deduplicate
    const uniqueCompleted = [...new Set(completed)]
    initSteps(uniqueCompleted, current)
    initRef.current = id
  }, [id, documents, project, plan, docsFetched, planFetched, initSteps])

  // Auto-generate all modules once documents are all ready and plan doesn't exist yet
  useEffect(() => {
    if (!docsFetched || !planFetched) return
    if (autoGenRef.current) return
    if (!documents || documents.length === 0) return

    const SUCCESS = new Set(["processed", "completed"])
    const allDocsReady = documents.every((d) => SUCCESS.has(d.status))
    if (!allDocsReady) return

    // Plan already exists — no need to auto-generate
    if (plan) return

    autoGenRef.current = true
    setAutoGenStatus("running")
    setAutoGenBannerVisible(true)

    const run = async () => {
      try {
        // Fire combined analysis in background (don't await — improves LLM context quality)
        documentService.analyzeCombined(id).catch(() => {/* best-effort */})

        // Generate plan + checklist in parallel
        await Promise.allSettled([
          bidPlanService.generatePlan(id),
          checklistService.generate(id, false),
        ])

        // Invalidate all relevant caches
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: ["project", id] }),
          queryClient.invalidateQueries({ queryKey: ["bid-plan", id] }),
          queryClient.invalidateQueries({ queryKey: ["bid-plan-tasks", id] }),
          queryClient.invalidateQueries({ queryKey: ["checklist", id] }),
        ])

        setAutoGenStatus("done")
        goToStep("plan")

        // Auto-hide success banner after 4s
        setTimeout(() => setAutoGenBannerVisible(false), 4000)
      } catch {
        setAutoGenStatus("error")
      }
    }

    run()
  }, [id, documents, plan, docsFetched, planFetched, queryClient, goToStep])

  // Reset autoGenRef when project id changes so the effect can re-fire on a new project
  useEffect(() => {
    autoGenRef.current = false
    setAutoGenStatus("idle")
    setAutoGenBannerVisible(false)
  }, [id])

  const isFullscreen = chatMode === "fullscreen"

  return (
    <div className="app-shell flex h-screen flex-col">
      {/* Header */}
      <header className="px-4 py-4">
        <div className="app-section-frame mx-auto flex max-w-[1440px] items-center justify-between gap-4 px-4 py-3">
          <div className="flex items-center gap-3">
            <Button asChild variant="outline" size="sm">
              <Link href={`/${locale}/projects/${id}`}>{t("back")}</Link>
            </Button>
            <span className="landing-v2-display text-base font-semibold text-slate-900">
              {project?.name || t("title")}
            </span>
          </div>
          <Button onClick={toggleChatPanel} variant="outline" size="sm">
            {isChatPanelOpen ? t("hideAI") : t("showAI")}
          </Button>
        </div>
      </header>

      {/* Auto-generation status banner */}
      {autoGenBannerVisible && autoGenStatus !== "idle" && (
        <div className="mx-auto w-full max-w-[1440px] px-4 pb-2">
          <div
            className={`flex items-center gap-3 rounded-xl px-4 py-2.5 text-sm font-medium ${
              autoGenStatus === "running"
                ? "bg-blue-50 text-blue-800 border border-blue-200"
                : autoGenStatus === "done"
                  ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                  : "bg-red-50 text-red-800 border border-red-200"
            }`}
          >
            {autoGenStatus === "running" && (
              <span className="h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />
            )}
            {autoGenStatus === "done" && <span>✅</span>}
            {autoGenStatus === "error" && <span>⚠️</span>}
            <span className="flex-1">
              {autoGenStatus === "running"
                ? t("autoGen.running")
                : autoGenStatus === "done"
                  ? t("autoGen.done")
                  : t("autoGen.error")}
            </span>
            {autoGenStatus === "error" && (
              <button
                onClick={() => setAutoGenBannerVisible(false)}
                className="ml-auto shrink-0 opacity-60 hover:opacity-100"
              >
                ✕
              </button>
            )}
          </div>
        </div>
      )}

      {/* Three-column layout — fullscreen hides nav + workspace */}
      <div className="mx-auto flex w-full max-w-[1440px] flex-1 gap-4 overflow-hidden px-4 pb-4">
        {!isFullscreen && <BidProgressNav />}
        {!isFullscreen && <BidWorkspace projectId={id} />}
        <BidChatPanel projectId={id} />
      </div>
    </div>
  )
}
