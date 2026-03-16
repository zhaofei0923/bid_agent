"use client"

import { memo } from "react"
import { useQuery } from "@tanstack/react-query"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { bidPlanService } from "@/services/bid-plan"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useTranslations } from "next-intl"

interface TrackingStepProps {
  projectId: string
}

export const TrackingStep = memo(function TrackingStep({
  projectId,
}: TrackingStepProps) {
  const { completedSteps } = useBidWorkspaceStore()
  const t = useTranslations("bid")

  const { data: tasks, isLoading } = useQuery({
    queryKey: ["bid-plan-tasks", projectId],
    queryFn: () => bidPlanService.listTasks(projectId),
    enabled: !!projectId,
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  const totalTasks = tasks?.length || 0
  const completedTasks =
    tasks?.filter((t) => t.status === "completed").length || 0
  const progressPercent = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">{t("tracking.title")}</h2>
        <p className="text-muted-foreground text-sm mt-1">
          {t("tracking.subtitle")}
        </p>
      </div>

      {/* Steps progress */}
      <Card>
        <CardHeader className="pb-2">
          <h3 className="text-sm font-semibold">{t("tracking.stepsProgress")}</h3>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[
              "upload",
              "overview",
              "plan",
              "writing",
              "review",
            ].map((step) => (
              <div key={step} className="flex items-center gap-3">
                <span className="text-sm">
                  {completedSteps.includes(step as never) ? "✅" : "⬜"}
                </span>
                <span className="text-sm capitalize">{step}</span>
              </div>
            ))}
          </div>
          <p className="mt-3 text-sm text-muted-foreground">
            {t("tracking.stepsCompleted", { completed: completedSteps.length })}
          </p>
        </CardContent>
      </Card>

      {/* Task progress */}
      <Card>
        <CardHeader className="pb-2">
          <h3 className="text-sm font-semibold">{t("tracking.taskProgress")}</h3>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>
                {t("tracking.tasksCompleted", { completed: completedTasks, total: totalTasks })}
              </span>
              <span>{Math.round(progressPercent)}%</span>
            </div>
            <div className="h-2 rounded-full bg-muted overflow-hidden">
              <div
                className="h-full rounded-full bg-primary transition-all duration-500"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {tasks && tasks.length > 0 && (
            <div className="mt-4 space-y-1">
              {tasks
                .filter((t) => t.status !== "completed")
                .slice(0, 5)
                .map((task) => (
                  <div
                    key={task.id}
                    className="flex items-center justify-between py-1.5 text-sm"
                  >
                    <span>{task.title}</span>
                    <span className="text-xs text-muted-foreground">
                      {task.due_date
                        ? t("tracking.dueDate", { date: task.due_date })
                        : t("tracking.noDueDate")}
                    </span>
                  </div>
                ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
})
