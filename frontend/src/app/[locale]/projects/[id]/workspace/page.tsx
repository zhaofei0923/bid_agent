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
import { Button } from "@/components/ui/button"

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
