"use client"

import { memo, useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { bidPlanService } from "@/services/bid-plan"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { useTranslations } from "next-intl"
import type { BidPlanTask } from "@/types/bid"

interface PlanStepProps {
  projectId: string
}

const CATEGORY_STYLES: Record<string, { label: string; cls: string }> = {
  compliance: { label: "合规", cls: "bg-red-100 text-red-700" },
  technical: { label: "技术", cls: "bg-blue-100 text-blue-700" },
  commercial: { label: "商务", cls: "bg-amber-100 text-amber-700" },
  administrative: { label: "行政", cls: "bg-slate-100 text-slate-600" },
}

const PRIORITY_STYLES: Record<string, { label: string; cls: string }> = {
  high: { label: "高", cls: "bg-rose-50 text-rose-600 border border-rose-200" },
  medium: { label: "中", cls: "bg-yellow-50 text-yellow-600 border border-yellow-200" },
  low: { label: "低", cls: "bg-green-50 text-green-600 border border-green-200" },
}

export const PlanStep = memo(function PlanStep({ projectId }: PlanStepProps) {
  const { completeStep, goToStep } = useBidWorkspaceStore()
  const t = useTranslations("bid")
  const queryClient = useQueryClient()
  const [newTaskTitle, setNewTaskTitle] = useState("")

  const { isLoading: planLoading } = useQuery({
    queryKey: ["bid-plan", projectId],
    queryFn: () => bidPlanService.getByProject(projectId),
    enabled: !!projectId,
    retry: false,
  })

  const { data: tasks, isLoading: tasksLoading } = useQuery({
    queryKey: ["bid-plan-tasks", projectId],
    queryFn: () => bidPlanService.listTasks(projectId),
    enabled: !!projectId,
    retry: false,
  })

  const generateMutation = useMutation({
    mutationFn: () => bidPlanService.generatePlan(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bid-plan", projectId] })
      queryClient.invalidateQueries({ queryKey: ["bid-plan-tasks", projectId] })
    },
  })

  const addTaskMutation = useMutation({
    mutationFn: (title: string) =>
      bidPlanService.addTask(projectId, { title }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bid-plan-tasks", projectId] })
      setNewTaskTitle("")
    },
  })

  const updateTaskMutation = useMutation({
    mutationFn: ({
      taskId,
      status,
    }: {
      taskId: string
      status: string
    }) => bidPlanService.updateTask(projectId, taskId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bid-plan-tasks", projectId] })
    },
  })

  const handleNext = () => {
    completeStep("plan")
    goToStep("writing")
  }

  if (planLoading || tasksLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-48 w-full" />
      </div>
    )
  }

  const statusColors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-800",
    in_progress: "bg-blue-100 text-blue-800",
    completed: "bg-green-100 text-green-800",
  }

  const taskList: BidPlanTask[] = Array.isArray(tasks) ? tasks : []

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold">{t("plan.title")}</h2>
          <p className="text-muted-foreground text-sm mt-1">
            {t("plan.subtitle")}
          </p>
        </div>
        <Button
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
          className="shrink-0"
        >
          {generateMutation.isPending ? (
            <>
              <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              {t("plan.generating")}
            </>
          ) : (
            <>✨ {t("plan.generateBtn")}</>
          )}
        </Button>
      </div>

      {generateMutation.isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          AI 生成失败，请稍后重试
        </div>
      )}

      {/* Task list */}
      <Card>
        <CardHeader className="pb-2">
          <h3 className="text-sm font-semibold">{t("plan.taskList")}</h3>
        </CardHeader>
        <CardContent>
          {taskList.length > 0 ? (
            <div className="space-y-2">
              {taskList.map((task) => {
                const catStyle = CATEGORY_STYLES[task.category ?? ""] ?? null
                const priStyle = PRIORITY_STYLES[task.priority ?? ""] ?? null
                return (
                  <div
                    key={task.id}
                    className="flex items-start justify-between gap-3 rounded-lg border border-slate-100 bg-slate-50/50 px-3 py-2.5"
                  >
                    <div className="flex min-w-0 items-start gap-3">
                      <input
                        type="checkbox"
                        checked={task.status === "completed"}
                        onChange={() =>
                          updateTaskMutation.mutate({
                            taskId: task.id,
                            status:
                              task.status === "completed"
                                ? "pending"
                                : "completed",
                          })
                        }
                        className="mt-0.5 h-4 w-4 shrink-0 rounded border-gray-300"
                      />
                      <div className="min-w-0 space-y-1">
                        <span
                          className={`block text-sm leading-snug ${
                            task.status === "completed"
                              ? "line-through text-muted-foreground"
                              : "font-medium"
                          }`}
                        >
                          {task.title}
                        </span>
                        {task.description && (
                          <p className="line-clamp-2 text-xs text-slate-500">
                            {task.description}
                          </p>
                        )}
                        <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                          {catStyle && (
                            <span className={`rounded px-1.5 py-0.5 text-[11px] font-medium ${catStyle.cls}`}>
                              {catStyle.label}
                            </span>
                          )}
                          {priStyle && (
                            <span className={`rounded px-1.5 py-0.5 text-[11px] font-medium ${priStyle.cls}`}>
                              {priStyle.label}优先
                            </span>
                          )}
                          {task.due_date && (
                            <span className="text-[11px] text-slate-400">
                              截止 {task.due_date}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <Badge
                      variant="secondary"
                      className={`shrink-0 text-xs ${statusColors[task.status] || ""}`}
                    >
                      {task.status === "pending"
                        ? t("plan.statusPending")
                        : task.status === "in_progress"
                          ? t("plan.statusInProgress")
                          : t("plan.statusCompleted")}
                    </Badge>
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="py-4 text-center text-sm text-muted-foreground">
              {generateMutation.isPending ? "正在生成任务清单…" : t("plan.noTasks")}
            </p>
          )}

          {/* Add task */}
          <div className="mt-4 flex gap-2">
            <Input
              value={newTaskTitle}
              onChange={(e) => setNewTaskTitle(e.target.value)}
              onKeyDown={(e) =>
                e.key === "Enter" &&
                newTaskTitle.trim() &&
                addTaskMutation.mutate(newTaskTitle.trim())
              }
              placeholder={t("plan.addTaskPlaceholder")}
              className="text-sm"
            />
            <Button
              size="sm"
              variant="outline"
              onClick={() =>
                newTaskTitle.trim() &&
                addTaskMutation.mutate(newTaskTitle.trim())
              }
              disabled={!newTaskTitle.trim() || addTaskMutation.isPending}
            >
              {t("plan.addButton")}
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button onClick={handleNext}>{t("plan.nextStep")}</Button>
      </div>
    </div>
  )
})
