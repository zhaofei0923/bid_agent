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
import { FolderOpen, Trash2 } from "lucide-react"
import type { ProjectStatus } from "@/types/project"

const STATUS_LABEL: Record<ProjectStatus, string> = {
  draft: "草稿",
  created: "进行中",
  analyzing: "分析中",
  analyzed: "已分析",
  guiding: "指导中",
  completed: "已完成",
  archived: "已归档",
}

const STATUS_VARIANT: Record<ProjectStatus, "secondary" | "outline" | "default" | "destructive"> = {
  draft: "outline",
  created: "secondary",
  analyzing: "secondary",
  analyzed: "default",
  guiding: "default",
  completed: "default",
  archived: "outline",
}

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

  const deleteMutation = useMutation({
    mutationFn: (id: string) => projectService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] })
    },
    onError: () => {
      alert("删除失败，请重试")
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] })
    },
  })

  const handleDelete = (e: React.MouseEvent, projectId: string, projectName: string) => {
    e.preventDefault()
    e.stopPropagation()
    if (!window.confirm(`确定要删除项目「${projectName}」吗？此操作不可撤销。`)) return
    deleteMutation.mutate(projectId)
  }

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
              <div key={project.id} className="relative">
                <Link
                  href={`/${locale}/projects/${project.id}`}
                  className="block"
                >
                  <Card className="app-card-interactive h-full">
                    <CardHeader>
                      <div className="flex items-start justify-between gap-4 pr-8">
                        <CardTitle className="text-xl">{project.name}</CardTitle>
                        <Badge variant={STATUS_VARIANT[project.status as ProjectStatus] ?? "secondary"}>
                          {STATUS_LABEL[project.status as ProjectStatus] ?? project.status}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      {project.description && (
                        <p className="line-clamp-2 text-sm leading-7 text-stone-600">
                          {project.description}
                        </p>
                      )}
                      <div className="mt-5 flex items-center justify-between text-sm text-stone-500">
                        <span>{t("progress")} {project.progress}%</span>
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
                <button
                  type="button"
                  onClick={(e) => handleDelete(e, project.id, project.name)}
                  disabled={deleteMutation.isPending}
                  className="absolute right-3 top-3 z-10 rounded p-1 text-stone-400 transition-colors hover:bg-red-50 hover:text-red-500"
                  title="删除项目"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
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
