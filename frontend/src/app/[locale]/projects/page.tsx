"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { projectService } from "@/services/projects"
import { formatRelative } from "@/lib/utils"
import { MainLayout } from "@/components/layout/MainLayout"
import { AppPageShell } from "@/components/layout/AppPageShell"
import { AppEmptyState } from "@/components/layout/AppEmptyState"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { FolderOpen } from "lucide-react"

export default function ProjectsPage() {
  const t = useTranslations("projects")
  const tc = useTranslations("common")
  const queryClient = useQueryClient()
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState("")
  const [newDesc, setNewDesc] = useState("")
  const [newInstitution, setNewInstitution] = useState<"adb" | "wb" | "other">("adb")

  const { data, isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: () => projectService.list(),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      projectService.create({ name: newName, description: newDesc || undefined, institution: newInstitution }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] })
      setShowCreate(false)
      setNewName("")
      setNewDesc("")
      setNewInstitution("adb")
    },
  })

  return (
    <MainLayout>
      <AppPageShell
        eyebrow={t("status")}
        title={t("title")}
        description={t("noProjects")}
        actions={
          <Button onClick={() => setShowCreate(true)}>
            + {t("create")}
          </Button>
        }
      >

        {/* Create Dialog */}
        {showCreate && (
          <div className="app-section-frame px-6 py-6 sm:px-8">
            <h3 className="app-section-title">{t("create")}</h3>
            <div className="mt-5 space-y-4">
              <Input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder={t("name")}
              />
              <Textarea
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                placeholder={t("description")}
                rows={3}
              />
              <div className="space-y-1">
                <label className="text-sm font-medium text-slate-700">{t("institution")}</label>
                <div className="flex gap-2">
                  {(["adb", "wb", "other"] as const).map((inst) => (
                    <button
                      key={inst}
                      type="button"
                      onClick={() => setNewInstitution(inst)}
                      className={`rounded-lg border px-3 py-2 text-sm transition-colors ${
                        newInstitution === inst
                          ? "border-blue-500 bg-blue-50 text-blue-700 font-medium"
                          : "border-slate-200 text-slate-600 hover:border-slate-300"
                      }`}
                    >
                      {t(inst === "adb" ? "institutionAdb" : inst === "wb" ? "institutionWb" : "institutionOther")}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={() => createMutation.mutate()}
                  disabled={!newName || createMutation.isPending}
                >
                  {t("create")}
                </Button>
                <Button onClick={() => setShowCreate(false)} variant="outline">
                  {tc("cancel")}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Project List */}
        {isLoading ? (
          <div className="app-surface px-6 py-12 text-center text-stone-500">{tc("loading")}</div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {data?.items.map((project) => (
              <Link
                key={project.id}
                href={`/${locale}/projects/${project.id}`}
                className="block"
              >
                <Card className="app-card-interactive h-full">
                  <CardHeader>
                    <div className="flex items-start justify-between gap-4">
                      <CardTitle className="text-xl">{project.name}</CardTitle>
                      <Badge variant="secondary">{project.status}</Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {project.description && (
                      <p className="line-clamp-2 text-sm leading-7 text-stone-600">
                        {project.description}
                      </p>
                    )}
                    <div className="mt-5 flex items-center justify-between text-sm text-stone-500">
                      <span>{t("progress")}</span>
                      <span>{formatRelative(project.created_at)}</span>
                    </div>
                    <div className="app-progress-track mt-3">
                      <div
                        className="app-progress-fill"
                        style={{ width: `${project.progress}%` }}
                      />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
            {data?.items.length === 0 && (
              <div className="col-span-full">
                <AppEmptyState
                  title={t("noProjects")}
                  icon={<FolderOpen className="h-5 w-5" />}
                />
              </div>
            )}
          </div>
        )}
      </AppPageShell>
    </MainLayout>
  )
}
