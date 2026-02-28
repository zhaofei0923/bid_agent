"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { projectService } from "@/services/projects"
import { formatRelative } from "@/lib/utils"
import { MainLayout } from "@/components/layout/MainLayout"

export default function ProjectsPage() {
  const t = useTranslations("projects")
  const tc = useTranslations("common")
  const queryClient = useQueryClient()
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState("")
  const [newDesc, setNewDesc] = useState("")

  const { data, isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: () => projectService.list(),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      projectService.create({ name: newName, description: newDesc || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] })
      setShowCreate(false)
      setNewName("")
      setNewDesc("")
    },
  })

  return (
    <MainLayout>
      <main className="container mx-auto px-6 py-8">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">{t("title")}</h1>
          <button
            onClick={() => setShowCreate(true)}
            className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 transition"
          >
            + {t("create")}
          </button>
        </div>

        {/* Create Dialog */}
        {showCreate && (
          <div className="mt-4 rounded-xl border bg-white p-6">
            <h3 className="text-lg font-semibold">{t("create")}</h3>
            <div className="mt-4 space-y-3">
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder={t("name")}
                className="w-full rounded-lg border px-3 py-2"
              />
              <textarea
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                placeholder={t("description")}
                rows={3}
                className="w-full rounded-lg border px-3 py-2"
              />
              <div className="flex gap-2">
                <button
                  onClick={() => createMutation.mutate()}
                  disabled={!newName || createMutation.isPending}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
                >
                  {t("create")}
                </button>
                <button
                  onClick={() => setShowCreate(false)}
                  className="rounded-lg border px-4 py-2"
                >
                  {tc("cancel")}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Project List */}
        {isLoading ? (
          <div className="mt-8 text-center text-gray-500">{tc("loading")}</div>
        ) : (
          <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {data?.items.map((project) => (
              <Link
                key={project.id}
                href={`/${locale}/projects/${project.id}`}
                className="rounded-xl border bg-white p-6 hover:shadow-md transition"
              >
                <h3 className="text-lg font-semibold">{project.name}</h3>
                {project.description && (
                  <p className="mt-1 text-sm text-gray-600 line-clamp-2">
                    {project.description}
                  </p>
                )}
                <div className="mt-4 flex items-center justify-between text-sm">
                  <span className="rounded bg-blue-100 px-2 py-0.5 text-blue-700">
                    {project.status}
                  </span>
                  <span className="text-gray-400">
                    {formatRelative(project.created_at)}
                  </span>
                </div>
                <div className="mt-3">
                  <div className="h-2 rounded-full bg-gray-100">
                    <div
                      className="h-2 rounded-full bg-blue-600"
                      style={{ width: `${project.progress}%` }}
                    />
                  </div>
                </div>
              </Link>
            ))}
            {data?.items.length === 0 && (
              <p className="col-span-full text-center text-gray-500 py-12">
                {t("noProjects")}
              </p>
            )}
          </div>
        )}
      </main>
    </MainLayout>
  )
}
