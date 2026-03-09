"use client"

import { useEffect, useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import type { BidPlanTask, TaskCategory } from "@/types/bid"

const CATEGORY_OPTIONS: { value: TaskCategory; label: string }[] = [
  { value: "documents",  label: "文件资料" },
  { value: "team",       label: "团队组建" },
  { value: "technical",  label: "技术方案" },
  { value: "experience", label: "业绩经验" },
  { value: "financial",  label: "财务报价" },
  { value: "compliance", label: "合规审查" },
  { value: "submission", label: "提交装订" },
  { value: "review",     label: "评审检查" },
]

const PRIORITY_OPTIONS = [
  { value: "high",   label: "高优先" },
  { value: "medium", label: "中优先" },
  { value: "low",    label: "低优先" },
]

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
  onSave?: (taskId: string, fields: Record<string, unknown>) => void
  isPending?: boolean
}

export function TaskDetailDialog({
  task,
  open,
  onOpenChange,
  onStatusChange,
  onSave,
  isPending = false,
}: TaskDetailDialogProps) {
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [category, setCategory] = useState<string>("")
  const [priority, setPriority] = useState<string>("")
  const [dueDate, setDueDate] = useState("")
  const [assignee, setAssignee] = useState("")
  const [notes, setNotes] = useState("")

  // Sync form when task changes
  useEffect(() => {
    if (task) {
      setTitle(task.title ?? "")
      setDescription(task.description ?? "")
      setCategory(task.category ?? "")
      setPriority(task.priority ?? "")
      setDueDate(task.due_date ?? "")
      setAssignee(task.assigned_to ?? "")
      setNotes(task.notes ?? "")
    }
  }, [task])

  if (!task) return null

  const handleSave = () => {
    if (!onSave) return
    onSave(task.id, {
      title: title.trim() || task.title,
      description: description || null,
      category: category || null,
      priority: priority || null,
      due_date: dueDate || null,
      assigned_to: assignee || null,
      notes: notes || null,
    })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>编辑任务</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* 任务名称 */}
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-500">任务名称</label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>

          {/* 任务说明 */}
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-500">任务说明</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
            />
          </div>

          {/* 分类 & 优先级 */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-500">分类</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
              >
                <option value="">未分类</option>
                {CATEGORY_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-500">优先级</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
              >
                <option value="">未设置</option>
                {PRIORITY_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* 截止日期 & 负责人 */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-500">截止日期</label>
              <Input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-500">负责人</label>
              <Input value={assignee} onChange={(e) => setAssignee(e.target.value)} placeholder="输入负责人" />
            </div>
          </div>

          {/* 备注 */}
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-500">备注</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
              placeholder="补充备注信息"
            />
          </div>

          {/* 关联文件信息（只读展示） */}
          {(task.related_document || task.reference_page) && (
            <div className="rounded-lg bg-slate-50 px-4 py-3">
              <p className="mb-1 text-xs font-semibold text-slate-500">关联招标文件</p>
              <p className="text-sm text-slate-700">
                {task.related_document ?? "—"}
                {task.reference_page ? ` (第 ${task.reference_page} 页)` : ""}
              </p>
            </div>
          )}

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

          {/* 操作按钮 */}
          <div className="flex justify-end gap-2 pt-1">
            <Button variant="outline" size="sm" onClick={() => onOpenChange(false)}>
              取消
            </Button>
            <Button size="sm" onClick={handleSave} disabled={isPending}>
              保存
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
