"use client"

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import type { BidPlanTask } from "@/types/bid"

const CATEGORY_LABELS: Record<string, string> = {
  compliance:     "合规",
  technical:      "技术",
  commercial:     "商务",
  administrative: "行政",
}

const CATEGORY_CLS: Record<string, string> = {
  compliance:     "bg-red-100 text-red-700",
  technical:      "bg-blue-100 text-blue-700",
  commercial:     "bg-amber-100 text-amber-700",
  administrative: "bg-slate-100 text-slate-600",
}

const PRIORITY_LABELS: Record<string, string> = {
  high:   "高优先",
  medium: "中优先",
  low:    "低优先",
}

const PRIORITY_CLS: Record<string, string> = {
  high:   "bg-rose-50 text-rose-600 border border-rose-200",
  medium: "bg-yellow-50 text-yellow-600 border border-yellow-200",
  low:    "bg-green-50 text-green-600 border border-green-200",
}

const STATUS_LIST = [
  { value: "pending",     label: "待处理",  cls: "border-yellow-300 text-yellow-700 hover:bg-yellow-50" },
  { value: "in_progress", label: "进行中",  cls: "border-blue-300   text-blue-700   hover:bg-blue-50"   },
  { value: "completed",   label: "已完成",  cls: "border-green-300  text-green-700  hover:bg-green-50"  },
]

interface TaskDetailDialogProps {
  task: BidPlanTask | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onStatusChange: (taskId: string, status: string) => void
  isPending?: boolean
}

export function TaskDetailDialog({
  task,
  open,
  onOpenChange,
  onStatusChange,
  isPending = false,
}: TaskDetailDialogProps) {
  if (!task) return null

  const catLabel = CATEGORY_LABELS[task.category ?? ""] ?? task.category ?? "—"
  const catCls   = CATEGORY_CLS[task.category ?? ""] ?? "bg-gray-100 text-gray-600"
  const priLabel = PRIORITY_LABELS[task.priority ?? ""] ?? task.priority ?? "—"
  const priCls   = PRIORITY_CLS[task.priority ?? ""] ?? "bg-gray-50 text-gray-500 border border-gray-200"

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{task.title}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* 分类 & 优先级 */}
          <div className="flex flex-wrap gap-2">
            <span className={`rounded px-2 py-0.5 text-xs font-medium ${catCls}`}>
              {catLabel}
            </span>
            <span className={`rounded px-2 py-0.5 text-xs font-medium ${priCls}`}>
              {priLabel}
            </span>
            <span className={`ml-auto rounded px-2 py-0.5 text-xs font-medium ${
              task.status === "completed"
                ? "bg-green-100 text-green-700"
                : task.status === "in_progress"
                  ? "bg-blue-100 text-blue-700"
                  : "bg-yellow-100 text-yellow-700"
            }`}>
              {task.status === "completed" ? "已完成" : task.status === "in_progress" ? "进行中" : "待处理"}
            </span>
          </div>

          {/* 详细描述 */}
          {task.description ? (
            <div className="rounded-lg bg-slate-50 px-4 py-3">
              <p className="mb-1 text-xs font-semibold text-slate-500">任务说明</p>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
                {task.description}
              </p>
            </div>
          ) : (
            <div className="rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-400">
              暂无详细说明
            </div>
          )}

          {/* 元信息 */}
          <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
            {task.due_date && (
              <>
                <span className="text-slate-500">截止日期</span>
                <span className="font-medium text-slate-700">{task.due_date}</span>
              </>
            )}
            {task.assigned_to && (
              <>
                <span className="text-slate-500">负责人</span>
                <span className="font-medium text-slate-700">{task.assigned_to}</span>
              </>
            )}
          </div>

          {/* 状态切换 */}
          <div>
            <p className="mb-2 text-xs font-semibold text-slate-500">更新状态</p>
            <div className="flex gap-2">
              {STATUS_LIST.map((s) => (
                <button
                  key={s.value}
                  disabled={isPending || task.status === s.value}
                  onClick={() => onStatusChange(task.id, s.value)}
                  className={`flex-1 rounded-lg border py-1.5 text-xs font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
                    task.status === s.value
                      ? s.cls + " opacity-100 font-semibold bg-white"
                      : s.cls + " bg-transparent"
                  }`}
                >
                  {task.status === s.value && <span className="mr-1">✓</span>}
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {/* 关闭按钮 */}
          <div className="flex justify-end pt-1">
            <Button variant="outline" size="sm" onClick={() => onOpenChange(false)}>
              关闭
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
