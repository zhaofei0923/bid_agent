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
    <div className="flex h-screen flex-col">
      {/* Header */}
      <header className="flex items-center justify-between border-b bg-background px-4 py-2">
        <div className="flex items-center gap-3">
          <Link
            href={`/${locale}/projects/${id}`}
            className="text-muted-foreground hover:text-foreground text-sm"
          >
            {t("back")}
          </Link>
          <span className="font-semibold text-sm">
            {project?.name || t("title")}
          </span>
        </div>
        <button
          onClick={toggleChatPanel}
          className="rounded-lg border px-3 py-1.5 text-sm hover:bg-muted transition-colors"
        >
          {isChatPanelOpen ? t("hideAI") : t("showAI")}
        </button>
      </header>

      {/* Three-column layout */}
      <div className="flex flex-1 overflow-hidden">
        <BidProgressNav />
        <BidWorkspace projectId={id} />
        <BidChatPanel projectId={id} />
      </div>
    </div>
  )
}
