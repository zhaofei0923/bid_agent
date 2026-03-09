"use client"

import { forwardRef, useMemo } from "react"
import type { BidPlanTask } from "@/types/bid"

// ── 分类配色（8 类，与 PlanStep 保持一致） ──────────────────────────
const CATEGORY_BAR: Record<string, { bar: string; bg: string; label: string }> = {
  documents:  { bar: "bg-slate-400",   bg: "bg-slate-50",   label: "文件资料" },
  team:       { bar: "bg-violet-400",  bg: "bg-violet-50",  label: "团队组建" },
  technical:  { bar: "bg-blue-400",    bg: "bg-blue-50",    label: "技术方案" },
  experience: { bar: "bg-cyan-400",    bg: "bg-cyan-50",    label: "业绩经验" },
  financial:  { bar: "bg-amber-400",   bg: "bg-amber-50",   label: "财务报价" },
  compliance: { bar: "bg-red-400",     bg: "bg-red-50",     label: "合规审查" },
  submission: { bar: "bg-emerald-400", bg: "bg-emerald-50", label: "提交装订" },
  review:     { bar: "bg-rose-400",    bg: "bg-rose-50",    label: "评审检查" },
}

const DEFAULT_BAR = { bar: "bg-gray-300", bg: "bg-gray-50", label: "其他" }

// ── 日期工具 ──────────────────────────────────────────────────────
function parseDate(s: string | null): Date | null {
  if (!s) return null
  const d = new Date(s)
  return isNaN(d.getTime()) ? null : d
}

function addDays(d: Date, n: number): Date {
  const r = new Date(d)
  r.setDate(r.getDate() + n)
  return r
}

function startOfWeek(d: Date): Date {
  const r = new Date(d)
  const day = r.getDay() // 0=Sun
  r.setDate(r.getDate() - day)
  r.setHours(0, 0, 0, 0)
  return r
}

function formatMMDD(d: Date): string {
  return `${d.getMonth() + 1}/${d.getDate()}`
}

// ── 日期派生规则 ───────────────────────────────────────────────────
// 如果任务没有 due_date，按 sort_order 推算一个临时日期（今天 + sort_order*7d）
function deriveTaskDates(
  tasks: BidPlanTask[],
  today: Date,
): Array<BidPlanTask & { _start: Date; _end: Date; _derived: boolean }> {
  return tasks.map((t) => {
    const due = parseDate(t.due_date)
    if (due) {
      const start = addDays(due, -7)
      return { ...t, _start: start, _end: due, _derived: false }
    }
    // 无日期：用 sort_order 推算
    const base = t.sort_order ?? 0
    const start = addDays(today, base * 7)
    const end = addDays(start, 7)
    return { ...t, _start: start, _end: end, _derived: true }
  })
}

// ── 生成周头列表 ──────────────────────────────────────────────────
function buildWeeks(minDate: Date, maxDate: Date): Date[] {
  const weeks: Date[] = []
  let cur = startOfWeek(minDate)
  const end = startOfWeek(addDays(maxDate, 7))
  while (cur <= end) {
    weeks.push(new Date(cur))
    cur = addDays(cur, 7)
  }
  return weeks
}

// ── 计算 bar 在时间轴中的位置 ────────────────────────────────────
function barPosition(
  taskStart: Date,
  taskEnd: Date,
  axisStart: Date,
  totalDays: number,
): { left: string; width: string } {
  const startOffset = Math.max(
    0,
    (taskStart.getTime() - axisStart.getTime()) / 86400000,
  )
  const endOffset = Math.max(
    startOffset + 0.5,
    (taskEnd.getTime() - axisStart.getTime()) / 86400000,
  )
  const left = ((startOffset / totalDays) * 100).toFixed(2)
  const width = (((endOffset - startOffset) / totalDays) * 100).toFixed(2)
  return { left: `${left}%`, width: `${width}%` }
}

// ── Props ────────────────────────────────────────────────────────
interface GanttViewProps {
  tasks: BidPlanTask[]
  onTaskClick: (task: BidPlanTask) => void
}

export const GanttView = forwardRef<HTMLDivElement, GanttViewProps>(
  function GanttView({ tasks, onTaskClick }, ref) {
    const today = useMemo(() => {
      const d = new Date()
      d.setHours(0, 0, 0, 0)
      return d
    }, [])

    const derived = useMemo(() => deriveTaskDates(tasks, today), [tasks, today])

    // 时间轴范围
    const { axisStart, axisEnd } = useMemo(() => {
      const starts = derived.map((t) => t._start)
      const ends = derived.map((t) => t._end)
      const min = starts.length ? new Date(Math.min(...starts.map((d) => d.getTime()))) : today
      const max = ends.length ? new Date(Math.max(...ends.map((d) => d.getTime()))) : addDays(today, 28)
      return {
        axisStart: startOfWeek(addDays(min, -7)),
        axisEnd: addDays(startOfWeek(max), 14),
      }
    }, [derived, today])

    const weeks = useMemo(() => buildWeeks(axisStart, axisEnd), [axisStart, axisEnd])
    const totalDays = (axisEnd.getTime() - axisStart.getTime()) / 86400000

    if (tasks.length === 0) {
      return (
        <div className="flex h-40 items-center justify-center text-sm text-muted-foreground">
          暂无任务，点击「AI 一键生成」创建任务计划
        </div>
      )
    }

    return (
      <div ref={ref} className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        {/* ── 时间轴 Header ── */}
        <div className="flex border-b border-slate-200 bg-slate-50">
          {/* 任务名称列 固定宽度 */}
          <div className="w-44 shrink-0 border-r border-slate-200 px-3 py-2 text-xs font-semibold text-slate-500">
            任务
          </div>
          {/* 周标题 */}
          <div className="relative flex flex-1">
            {weeks.map((w, i) => (
              <div
                key={i}
                className="flex-1 border-r border-slate-100 px-1 py-2 text-center text-[11px] text-slate-400 last:border-r-0"
              >
                {formatMMDD(w)}
              </div>
            ))}
          </div>
        </div>

        {/* ── 任务行 ── */}
        {derived.map((task) => {
          const style = CATEGORY_BAR[task.category ?? ""] ?? DEFAULT_BAR
          const { left, width } = barPosition(task._start, task._end, axisStart, totalDays)
          const isDone = task.status === "completed"
          const isProgress = task.status === "in_progress"

          return (
            <div
              key={task.id}
              className="flex items-center border-b border-slate-100 last:border-b-0 hover:bg-slate-50/70"
            >
              {/* 任务名列 */}
              <div className="w-44 shrink-0 border-r border-slate-100 px-3 py-3">
                <div className="flex items-center gap-1.5">
                  <span
                    className={`inline-block h-2 w-2 shrink-0 rounded-full ${style.bar}`}
                  />
                  <span
                    className={`truncate text-[12px] leading-tight ${
                      isDone ? "text-slate-400 line-through" : "font-medium text-slate-700"
                    }`}
                    title={task.title}
                  >
                    {task.title}
                  </span>
                </div>
                <div className="mt-0.5 pl-3.5 text-[11px] text-slate-400">
                  {style.label}
                  {task._derived && (
                    <span className="ml-1 text-slate-300">（推算）</span>
                  )}
                </div>
              </div>

              {/* 时间条区域 */}
              <div className="relative flex flex-1 items-center py-3" style={{ minHeight: 48 }}>
                {/* 周格背景线 */}
                {weeks.map((_, i) => (
                  <div
                    key={i}
                    className="absolute top-0 bottom-0 border-r border-slate-100"
                    style={{ left: `${((i + 1) / weeks.length) * 100}%` }}
                  />
                ))}

                {/* 今日线 */}
                {(() => {
                  const todayOffset =
                    (today.getTime() - axisStart.getTime()) / 86400000
                  if (todayOffset >= 0 && todayOffset <= totalDays) {
                    const todayLeft = `${((todayOffset / totalDays) * 100).toFixed(2)}%`
                    return (
                      <div
                        className="absolute top-0 bottom-0 w-px bg-rose-300 opacity-60"
                        style={{ left: todayLeft }}
                      />
                    )
                  }
                  return null
                })()}

                {/* 任务 Bar */}
                <button
                  onClick={() => onTaskClick(task)}
                  style={{ left, width }}
                  className={`absolute flex h-7 cursor-pointer items-center rounded-md px-2 text-left text-[11px] font-medium text-white shadow-sm transition-all hover:brightness-110 hover:shadow-md active:scale-[0.98] ${
                    isDone
                      ? "opacity-50 " + style.bar
                      : style.bar
                  } ${isProgress ? "ring-2 ring-white ring-offset-1" : ""}`}
                  title={`${task.title}（点击查看详情）`}
                >
                  {isDone && (
                    <span className="mr-1 text-[10px]">✓</span>
                  )}
                  {isProgress && (
                    <span className="mr-1 animate-pulse text-[10px]">●</span>
                  )}
                  <span className="truncate">{task.title}</span>
                </button>
              </div>
            </div>
          )
        })}

        {/* 图例 */}
        <div className="flex flex-wrap items-center gap-3 border-t border-slate-100 px-4 py-2">
          {Object.entries(CATEGORY_BAR).map(([key, s]) => (
            <span key={key} className="flex items-center gap-1 text-[11px] text-slate-500">
              <span className={`inline-block h-2 w-4 rounded-sm ${s.bar}`} />
              {s.label}
            </span>
          ))}
          <span className="flex items-center gap-1 text-[11px] text-slate-400">
            <span className="inline-block h-3 w-px bg-rose-300" />
            今日
          </span>
          <span className="ml-auto text-[11px] text-slate-400">点击任务条查看详情</span>
        </div>
      </div>
    )
  },
)
