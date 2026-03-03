"use client"

import { use } from "react"
import { useTranslations } from "next-intl"
import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { projectService } from "@/services/projects"
import { formatDate } from "@/lib/utils"
import { MainLayout } from "@/components/layout/MainLayout"
import { AppPageShell } from "@/components/layout/AppPageShell"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

export default function ProjectDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const t = useTranslations("projects")
  const tc = useTranslations("common")
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"

  const { data: project, isLoading } = useQuery({
    queryKey: ["project", id],
    queryFn: () => projectService.getById(id),
  })

  if (isLoading) return <MainLayout><div className="p-8 text-center">{tc("loading")}</div></MainLayout>
  if (!project) return <MainLayout><div className="p-8 text-center">{t("notFound")}</div></MainLayout>

  return (
    <MainLayout>
      <AppPageShell
        eyebrow={t("createdAt")}
        title={project.name}
        description={
          project.description ||
          t("createdOn", { date: formatDate(project.created_at) })
        }
        actions={
          <>
            <Button asChild variant="outline">
              <Link href={`/${locale}/projects`}>{tc("backToList")}</Link>
            </Button>
            <Button asChild>
              <Link href={`/${locale}/projects/${id}/workspace`}>
                {t("openWorkspace")}
              </Link>
            </Button>
          </>
        }
      >
        <div className="app-section-frame px-6 py-8 sm:px-8">
          <div className="flex flex-wrap items-center gap-3">
            <Badge variant="secondary">{project.status}</Badge>
            <span className="text-sm font-medium text-stone-500">
              {t("createdOn", { date: formatDate(project.created_at) })}
            </span>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <div className="app-surface-muted px-5 py-5">
              <p className="app-detail-label">{t("status")}</p>
              <p className="app-detail-value mt-2">{project.status}</p>
            </div>
            <div className="app-surface-muted px-5 py-5">
              <p className="app-detail-label">{t("progress")}</p>
              <p className="app-detail-value mt-2">{project.progress}%</p>
            </div>
            <div className="app-surface-muted px-5 py-5">
              <p className="app-detail-label">{t("currentStep")}</p>
              <p className="app-detail-value mt-2">{project.current_step || t("notStarted")}</p>
            </div>
          </div>

          <div className="mt-6">
            <div className="app-progress-track">
              <div
                className="app-progress-fill transition-all"
                style={{ width: `${project.progress}%` }}
              />
            </div>
          </div>
        </div>
      </AppPageShell>
    </MainLayout>
  )
}
