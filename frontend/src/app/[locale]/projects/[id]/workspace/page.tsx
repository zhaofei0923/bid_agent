"use client"

import { use, useEffect, useRef } from "react"
import { useTranslations } from "next-intl"
import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { projectService } from "@/services/projects"
import { documentService } from "@/services/documents"
import { bidAnalysisService } from "@/services/bid-analysis"
import { bidPlanService } from "@/services/bid-plan"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { BidProgressNav } from "@/components/bid/BidProgressNav"
import { BidWorkspace } from "@/components/bid/BidWorkspace"
import { BidChatPanel } from "@/components/bid/BidChatPanel"
import { Button } from "@/components/ui/button"
import type { BidStep } from "@/types"

export default function WorkspacePage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const t = useTranslations("workspace")
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"
  const { setProject, initSteps, isChatPanelOpen, toggleChatPanel } =
    useBidWorkspaceStore()
  const initRef = useRef<string | null>(null)

  const { data: project } = useQuery({
    queryKey: ["project", id],
    queryFn: () => projectService.getById(id),
  })

  const { data: documents, isFetched: docsFetched } = useQuery({
    queryKey: ["documents", id],
    queryFn: () => documentService.list(id),
    enabled: !!id,
  })

  const { data: analysis, isFetched: analysisFetched } = useQuery({
    queryKey: ["bid-analysis", id],
    queryFn: () => bidAnalysisService.getByProject(id),
    enabled: !!id,
    retry: false,
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
    if (!docsFetched || !analysisFetched || !planFetched) return

    const SUCCESS = new Set(["processed", "completed"])
    const hasProcessedDocs =
      !!documents && documents.length > 0 && documents.every((d) => SUCCESS.has(d.status))
    const hasOverview = !!project?.combined_ai_overview
    const hasAnalysis = !!analysis
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
      current = "analysis"
    }
    if (hasAnalysis) {
      if (!completed.includes("overview")) {
        completed.push("upload", "overview")
      }
      completed.push("analysis")
      current = "plan"
    }
    if (hasPlan) {
      if (!completed.includes("analysis")) {
        completed.push("upload", "overview", "analysis")
      }
      completed.push("plan")
      current = "writing"
    }

    // Deduplicate
    const uniqueCompleted = [...new Set(completed)]
    initSteps(uniqueCompleted, current)
    initRef.current = id
  }, [id, documents, project, analysis, plan, docsFetched, analysisFetched, planFetched, initSteps])

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

      {/* Three-column layout */}
      <div className="mx-auto flex w-full max-w-[1440px] flex-1 gap-4 overflow-hidden px-4 pb-4">
        <BidProgressNav />
        <BidWorkspace projectId={id} />
        <BidChatPanel projectId={id} />
      </div>
    </div>
  )
}
