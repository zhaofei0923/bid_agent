"use client"

import { memo, useCallback, useRef, useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { bidPlanService } from "@/services/bid-plan"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { useTranslations } from "next-intl"
import type { BidPlan, BidPlanTask } from "@/types/bid"
import { GanttView } from "./GanttView"
import { TaskDetailDialog } from "./TaskDetailDialog"

interface PlanStepProps {
  projectId: string
}

type ViewMode = "list" | "gantt"

const CATEGORY_STYLES: Record<string, { label: string; cls: string }> = {
  documents:  { label: "文件资料", cls: "bg-slate-100 text-slate-600" },
  team:       { label: "团队组建", cls: "bg-violet-100 text-violet-700" },
  technical:  { label: "技术方案", cls: "bg-blue-100 text-blue-700" },
  experience: { label: "业绩经验", cls: "bg-cyan-100 text-cyan-700" },
  financial:  { label: "财务报价", cls: "bg-amber-100 text-amber-700" },
  compliance: { label: "合规审查", cls: "bg-red-100 text-red-700" },
  submission: { label: "提交装订", cls: "bg-emerald-100 text-emerald-700" },
  review:     { label: "评审检查", cls: "bg-rose-100 text-rose-700" },
}

const PRIORITY_STYLES: Record<string, { label: string; cls: string }> = {
  high: { label: "高", cls: "bg-rose-50 text-rose-600 border border-rose-200" },
  medium: { label: "中", cls: "bg-yellow-50 text-yellow-600 border border-yellow-200" },
  low: { label: "低", cls: "bg-green-50 text-green-600 border border-green-200" },
}

// ── CSV 导出 ──────────────────────────────────────────────────────
function exportCsv(tasks: BidPlanTask[], filename = "bid_tasks.csv") {
  const CATEGORY_CN: Record<string, string> = {
    documents: "文件资料", team: "团队组建", technical: "技术方案",
    experience: "业绩经验", financial: "财务报价", compliance: "合规审查",
    submission: "提交装订", review: "评审检查",
  }
  const PRIORITY_CN: Record<string, string> = { high: "高", medium: "中", low: "低" }
  const STATUS_CN: Record<string, string> = {
    pending: "待处理", in_progress: "进行中", completed: "已完成",
  }
  const header = ["任务名称", "分类", "优先级", "截止日期", "状态", "负责人", "描述"]
  const rows = tasks.map((t) => [
    t.title,
    CATEGORY_CN[t.category ?? ""] ?? t.category ?? "",
    PRIORITY_CN[t.priority ?? ""] ?? t.priority ?? "",
    t.due_date ?? "",
    STATUS_CN[t.status] ?? t.status,
    t.assigned_to ?? "",
    (t.description ?? "").replace(/\n/g, " "),
  ])
  const csv = [header, ...rows]
    .map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(","))
    .join("\n")
  const bom = "\uFEFF" // UTF-8 BOM，确保 Excel 中文正常显示
  const blob = new Blob([bom + csv], { type: "text/csv;charset=utf-8;" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

// ── PNG 导出 ──────────────────────────────────────────────────────
async function exportPng(node: HTMLElement, filename = "gantt_plan.png") {
  const { toPng } = await import("html-to-image")
  const dataUrl = await toPng(node, {
    backgroundColor: "#ffffff",
    pixelRatio: 2,
    style: { fontFamily: "system-ui, sans-serif" },
  })
  const a = document.createElement("a")
  a.href = dataUrl
  a.download = filename
  a.click()
}

export const PlanStep = memo(function PlanStep({ projectId }: PlanStepProps) {
  const { completeStep, goToStep } = useBidWorkspaceStore()
  const t = useTranslations("bid")
  const queryClient = useQueryClient()
  const [newTaskTitle, setNewTaskTitle] = useState("")
  const [viewMode, setViewMode] = useState<ViewMode>("list")
  const [selectedTask, setSelectedTask] = useState<BidPlanTask | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)
  const [exportMenuOpen, setExportMenuOpen] = useState(false)
  const [dragIdx, setDragIdx] = useState<number | null>(null)
  const ganttRef = useRef<HTMLDivElement>(null)

  const { data: plan, isLoading: planLoading } = useQuery({
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

  const alreadyGenerated = !!(plan as BidPlan | null)?.generated_by_ai

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

  const updateFieldsMutation = useMutation({
    mutationFn: ({ taskId, fields }: { taskId: string; fields: Record<string, unknown> }) =>
      bidPlanService.updateTaskFields(projectId, taskId, fields),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bid-plan-tasks", projectId] })
    },
  })

  const reorderMutation = useMutation({
    mutationFn: (taskIds: string[]) =>
      bidPlanService.reorderTasks(projectId, taskIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bid-plan-tasks", projectId] })
    },
  })

  const handleNext = () => {
    completeStep("plan")
    goToStep("writing")
  }

  const handleTaskClick = (task: BidPlanTask) => {
    setSelectedTask(task)
    setDetailOpen(true)
  }

  const handleStatusChange = (taskId: string, status: string) => {
    updateTaskMutation.mutate({ taskId, status })
    setSelectedTask((prev) => prev ? { ...prev, status: status as BidPlanTask["status"] } : prev)
  }

  const handleSaveTask = useCallback(
    (taskId: string, fields: Record<string, unknown>) => {
      updateFieldsMutation.mutate({ taskId, fields })
      // optimistic update for the dialog
      setSelectedTask((prev) => prev && prev.id === taskId ? { ...prev, ...fields } as BidPlanTask : prev)
    },
    [updateFieldsMutation],
  )

  // ── Drag & Drop (list view) ──
  const handleDragStart = (idx: number) => setDragIdx(idx)
  const handleDragOver = (e: React.DragEvent) => e.preventDefault()
  const handleDrop = (targetIdx: number) => {
    if (dragIdx === null || dragIdx === targetIdx) return
    const ordered = [...taskList]
    const [moved] = ordered.splice(dragIdx, 1)
    ordered.splice(targetIdx, 0, moved)
    reorderMutation.mutate(ordered.map((t) => t.id))
    setDragIdx(null)
  }

  const handleExportCsv = () => {
    exportCsv(taskList)
    setExportMenuOpen(false)
  }

  const handleExportPng = async () => {
    if (ganttRef.current) {
      await exportPng(ganttRef.current)
    }
    setExportMenuOpen(false)
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
      {/* ── 标题行 ── */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">{t("plan.title")}</h2>
          <p className="text-muted-foreground text-sm mt-1">
            {t("plan.subtitle")}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* 视图切换 */}
          <div className="flex rounded-lg border border-stone-200 overflow-hidden text-sm">
            <button
              className={`px-3 py-1.5 font-medium transition-colors ${
                viewMode === "list"
                  ? "bg-slate-900 text-white"
                  : "bg-white text-stone-500 hover:text-slate-700"
              }`}
              onClick={() => setViewMode("list")}
            >
              ☰ 列表
            </button>
            <button
              className={`px-3 py-1.5 font-medium transition-colors ${
                viewMode === "gantt"
                  ? "bg-slate-900 text-white"
                  : "bg-white text-stone-500 hover:text-slate-700"
              }`}
              onClick={() => setViewMode("gantt")}
            >
              ▦ 甘特图
            </button>
          </div>

          {/* 导出下拉菜单 */}
          <div className="relative">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setExportMenuOpen((v) => !v)}
              disabled={taskList.length === 0}
            >
              ↓ 导出
            </Button>
            {exportMenuOpen && (
              <>
                {/* 点击外部关闭 */}
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setExportMenuOpen(false)}
                />
                <div className="absolute right-0 top-full z-20 mt-1 w-36 rounded-lg border border-stone-200 bg-white py-1 shadow-lg">
                  <button
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                    onClick={handleExportCsv}
                  >
                    📊 导出 CSV
                  </button>
                  {viewMode === "gantt" && (
                    <button
                      className="flex w-full items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                      onClick={handleExportPng}
                    >
                      📷 导出图片
                    </button>
                  )}
                </div>
              </>
            )}
          </div>

          {/* AI 生成 — 仅限一次 */}
          {alreadyGenerated ? (
            <span className="shrink-0 rounded-lg bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-500">
              ✅ 已由 AI 生成
            </span>
          ) : (
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
          )}
        </div>
      </div>

      {generateMutation.isError && (() => {
        const err = generateMutation.error as { code?: string; response?: { status?: number } } | null
        const isTimeout = err?.code === "ECONNABORTED"
        const isAuth = err?.response?.status === 401
        const isConflict = err?.response?.status === 409
        return (
          <div className={`rounded-lg border px-4 py-3 text-sm ${
            isConflict
              ? "border-amber-200 bg-amber-50 text-amber-700"
              : "border-red-200 bg-red-50 text-red-700"
          }`}>
            {isConflict
              ? "投标计划已由 AI 生成，不可重复生成。请手动编辑已有计划。"
              : isAuth
                ? "登录已过期，请重新登录后再试"
                : isTimeout
                  ? "AI 生成超时（通常需要 30-60 秒），请稍后重试"
                  : "AI 生成失败，请稍后重试"}
          </div>
        )
      })()}

      {/* ── 甘特图视图 ── */}
      {viewMode === "gantt" && (
        <GanttView
          ref={ganttRef}
          tasks={taskList}
          onTaskClick={handleTaskClick}
        />
      )}

      {/* ── 列表视图 ── */}
      {viewMode === "list" && (
        <Card>
          <CardHeader className="pb-2">
            <h3 className="text-sm font-semibold">{t("plan.taskList")}</h3>
          </CardHeader>
          <CardContent>
            {taskList.length > 0 ? (
              <div className="space-y-2">
                {taskList.map((task, idx) => {
                  const catStyle = CATEGORY_STYLES[task.category ?? ""] ?? null
                  const priStyle = PRIORITY_STYLES[task.priority ?? ""] ?? null
                  return (
                    <div
                      key={task.id}
                      draggable
                      onDragStart={() => handleDragStart(idx)}
                      onDragOver={handleDragOver}
                      onDrop={() => handleDrop(idx)}
                      className={`flex cursor-pointer items-start justify-between gap-3 rounded-lg border border-slate-100 bg-slate-50/50 px-3 py-2.5 hover:border-slate-200 hover:bg-slate-100/50 transition-colors ${
                        dragIdx === idx ? "opacity-50" : ""
                      }`}
                      onClick={() => handleTaskClick(task)}
                    >
                      <div className="flex min-w-0 items-start gap-3">
                        <input
                          type="checkbox"
                          checked={task.status === "completed"}
                          onChange={(e) => {
                            e.stopPropagation()
                            updateTaskMutation.mutate({
                              taskId: task.id,
                              status:
                                task.status === "completed"
                                  ? "pending"
                                  : "completed",
                            })
                          }}
                          onClick={(e) => e.stopPropagation()}
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
      )}

      {/* ── 任务详情弹窗 ── */}
      <TaskDetailDialog
        task={selectedTask}
        open={detailOpen}
        onOpenChange={setDetailOpen}
        onStatusChange={handleStatusChange}
        onSave={handleSaveTask}
        isPending={updateTaskMutation.isPending || updateFieldsMutation.isPending}
      />

      <div className="flex justify-end">
        <Button onClick={handleNext}>{t("plan.nextStep")}</Button>
      </div>
    </div>
  )
})
