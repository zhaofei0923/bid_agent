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
import { normalizeCategory } from "@/types/bid"
import { useTranslations } from "next-intl"

const CATEGORY_OPTIONS: { value: TaskCategory; labelKey: string }[] = [
  { value: "documents", labelKey: "categoryDocuments" },
  { value: "team", labelKey: "categoryTeam" },
  { value: "technical", labelKey: "categoryTechnical" },
  { value: "experience", labelKey: "categoryExperience" },
  { value: "financial", labelKey: "categoryFinancial" },
  { value: "compliance", labelKey: "categoryCompliance" },
  { value: "submission", labelKey: "categorySubmission" },
  { value: "review", labelKey: "categoryReview" },
]

const PRIORITY_OPTIONS = [
  { value: "high", labelKey: "priorityHigh" },
  { value: "medium", labelKey: "priorityMedium" },
  { value: "low", labelKey: "priorityLow" },
]

const STATUS_LIST = [
  { value: "pending", labelKey: "statusPending", cls: "border-yellow-300 text-yellow-700 hover:bg-yellow-50" },
  { value: "in_progress", labelKey: "statusInProgress", cls: "border-blue-300   text-blue-700   hover:bg-blue-50" },
  { value: "completed", labelKey: "statusCompleted", cls: "border-green-300  text-green-700  hover:bg-green-50" },
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
  const t = useTranslations("bid.plan.taskDialog")
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [category, setCategory] = useState<string>("")
  const [priority, setPriority] = useState<string>("")
  const [startDate, setStartDate] = useState("")
  const [dueDate, setDueDate] = useState("")
  const [assignee, setAssignee] = useState("")
  const [notes, setNotes] = useState("")

  // Sync form when task changes
  useEffect(() => {
    if (task) {
      setTitle(task.title ?? "")
      setDescription(task.description ?? "")
      setCategory(normalizeCategory(task.category) ?? "")
      setPriority(task.priority ?? "")
      setStartDate(task.start_date ?? "")
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
      start_date: startDate || null,
      due_date: dueDate || null,
      assigned_to: assignee || null,
      notes: notes || null,
    })
    onOpenChange?.(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{t("title")}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-500">{t("taskName")}</label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-500">{t("description")}</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-500">{t("category")}</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
              >
                <option value="">{t("uncategorized")}</option>
                {CATEGORY_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{t(o.labelKey)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-500">{t("priority")}</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
              >
                <option value="">{t("unset")}</option>
                {PRIORITY_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{t(o.labelKey)}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-500">{t("startDate")}</label>
              <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-500">{t("dueDate")}</label>
              <Input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-500">{t("assignee")}</label>
            <Input value={assignee} onChange={(e) => setAssignee(e.target.value)} placeholder={t("assigneePlaceholder")} />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-500">{t("notes")}</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
              placeholder={t("notesPlaceholder")}
            />
          </div>

          {(task.related_document || task.reference_page) && (
            <div className="rounded-lg bg-slate-50 px-4 py-3">
              <p className="mb-1 text-xs font-semibold text-slate-500">{t("relatedDocument")}</p>
              <p className="text-sm text-slate-700">
                {task.related_document ?? "—"}
                {task.reference_page ? t("pageRef", { page: task.reference_page }) : ""}
              </p>
            </div>
          )}

          <div>
            <p className="mb-2 text-xs font-semibold text-slate-500">{t("updateStatus")}</p>
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
                  {t(s.labelKey)}
                </button>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-1">
            <Button variant="outline" size="sm" onClick={() => onOpenChange(false)}>
              {t("cancel")}
            </Button>
            <Button size="sm" onClick={handleSave} disabled={isPending}>
              {t("save")}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
