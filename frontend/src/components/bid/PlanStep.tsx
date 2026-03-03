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

interface PlanStepProps {
  projectId: string
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
  })

  const { data: tasks, isLoading: tasksLoading } = useQuery({
    queryKey: ["bid-plan-tasks", projectId],
    queryFn: () => bidPlanService.listTasks(projectId),
    enabled: !!projectId,
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

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">{t("plan.title")}</h2>
        <p className="text-muted-foreground text-sm mt-1">
          {t("plan.subtitle")}
        </p>
      </div>

      {/* Task list */}
      <Card>
        <CardHeader className="pb-2">
          <h3 className="text-sm font-semibold">{t("plan.taskList")}</h3>
        </CardHeader>
        <CardContent>
          {tasks && tasks.length > 0 ? (
            <div className="space-y-2">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  className="flex items-center justify-between py-2 border-b last:border-0"
                >
                  <div className="flex items-center gap-3">
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
                      className="h-4 w-4 rounded border-gray-300"
                    />
                    <span
                      className={`text-sm ${
                        task.status === "completed"
                          ? "line-through text-muted-foreground"
                          : ""
                      }`}
                    >
                      {task.title}
                    </span>
                  </div>
                  <Badge
                    variant="secondary"
                    className={statusColors[task.status] || ""}
                  >
                    {task.status === "pending"
                      ? t("plan.statusPending")
                      : task.status === "in_progress"
                        ? t("plan.statusInProgress")
                        : t("plan.statusCompleted")}
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">{t("plan.noTasks")}</p>
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
