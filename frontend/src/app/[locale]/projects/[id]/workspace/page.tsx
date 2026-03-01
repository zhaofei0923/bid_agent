"use client"

import { use, useEffect } from "react"
import { useTranslations } from "next-intl"
import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { projectService } from "@/services/projects"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { BidProgressNav } from "@/components/bid/BidProgressNav"
import { BidWorkspace } from "@/components/bid/BidWorkspace"
import { BidChatPanel } from "@/components/bid/BidChatPanel"

export default function WorkspacePage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const t = useTranslations("workspace")
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"
  const { setProject, isChatPanelOpen, toggleChatPanel } =
    useBidWorkspaceStore()

  const { data: project } = useQuery({
    queryKey: ["project", id],
    queryFn: () => projectService.getById(id),
  })

  useEffect(() => {
    if (project) {
      setProject(id, project.institution || "adb")
    }
  }, [id, project, setProject])

  return (
    <div className="app-shell flex h-screen flex-col">
      {/* Header */}
      <header className="px-4 py-4">
        <div className="mx-auto flex max-w-[1440px] items-center justify-between gap-4 rounded-full border border-stone-300/90 bg-[rgba(255,252,247,0.96)] px-4 py-3 shadow-[0_20px_44px_-30px_rgba(15,23,42,0.18)]">
        <div className="flex items-center gap-3">
          <Link
            href={`/${locale}/projects/${id}`}
            className="text-sm font-medium text-stone-500 transition-colors duration-200 hover:text-slate-900"
          >
            {t("back")}
          </Link>
          <span className="landing-v2-display text-base font-semibold text-slate-900">
            {project?.name || t("title")}
          </span>
        </div>
        <button
          onClick={toggleChatPanel}
          className="inline-flex h-10 items-center rounded-full border border-stone-300 bg-white px-4 text-sm font-medium text-stone-600 transition-colors duration-200 hover:text-slate-900"
        >
          {isChatPanelOpen ? t("hideAI") : t("showAI")}
        </button>
        </div>
      </header>

      {/* Three-column layout */}
      <div className="mx-auto flex w-full max-w-[1440px] flex-1 overflow-hidden px-4 pb-4">
        <BidProgressNav />
        <BidWorkspace projectId={id} />
        <BidChatPanel projectId={id} />
      </div>
    </div>
  )
}
