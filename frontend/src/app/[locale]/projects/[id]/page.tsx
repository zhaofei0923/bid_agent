"use client"

import { use } from "react"
import { useTranslations } from "next-intl"
import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { projectService } from "@/services/projects"
import { formatDate } from "@/lib/utils"
import { MainLayout } from "@/components/layout/MainLayout"

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
      <main className="container mx-auto px-6 py-8">
        <Link href={`/${locale}/projects`} className="text-gray-500 hover:text-gray-700 text-sm">
          {tc("backToList")}
        </Link>

        <div className="mt-4 rounded-xl bg-white p-8 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">{project.name}</h1>
              <p className="mt-1 text-gray-500">
                {t("createdOn", { date: formatDate(project.created_at) })}
              </p>
            </div>
            <Link
              href={`/${locale}/projects/${id}/workspace`}
              className="rounded-lg bg-blue-600 px-6 py-2 text-white hover:bg-blue-700 transition"
            >
              {t("openWorkspace")}
            </Link>
          </div>

          {project.description && (
            <p className="mt-4 text-gray-700">{project.description}</p>
          )}

          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <div className="rounded-lg bg-gray-50 p-4">
              <p className="text-sm text-gray-500">{t("status")}</p>
              <p className="mt-1 font-semibold">{project.status}</p>
            </div>
            <div className="rounded-lg bg-gray-50 p-4">
              <p className="text-sm text-gray-500">{t("progress")}</p>
              <p className="mt-1 font-semibold">{project.progress}%</p>
            </div>
            <div className="rounded-lg bg-gray-50 p-4">
              <p className="text-sm text-gray-500">{t("currentStep")}</p>
              <p className="mt-1 font-semibold">{project.current_step || t("notStarted")}</p>
            </div>
          </div>

          <div className="mt-6">
            <div className="h-3 rounded-full bg-gray-100">
              <div
                className="h-3 rounded-full bg-blue-600 transition-all"
                style={{ width: `${project.progress}%` }}
              />
            </div>
          </div>
        </div>
      </main>
    </MainLayout>
  )
}
