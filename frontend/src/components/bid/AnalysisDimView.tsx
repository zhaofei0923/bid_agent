"use client"

import { Badge } from "@/components/ui/badge"
import type React from "react"

// ── Type helpers ─────────────────────────────────────────────────────────────
type Rec = Record<string, unknown>
/** Strip markdown emphasis markers (**bold**, *italic*, __bold__, _italic_) from LLM output. */
function stripMd(s: string): string {
  return s
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/__(.+?)__/g, "$1")
    .replace(/\*(.+?)\*/g, "$1")
    .replace(/_(.+?)_/g, "$1")
}
const str = (v: unknown): string => (typeof v === "string" ? stripMd(v) : "")
const num = (v: unknown): number => (typeof v === "number" ? v : 0)
const bool = (v: unknown): boolean => v === true
const arr = (v: unknown): unknown[] => (Array.isArray(v) ? v : [])
const rec = (v: unknown): Rec =>
  v && typeof v === "object" && !Array.isArray(v) ? (v as Rec) : {}

// ── Shared UI ─────────────────────────────────────────────────────────────────
function RiskBadge({ level }: { level: string }) {
  const MAP: Record<string, string> = {
    low: "bg-green-100 text-green-700",
    medium: "bg-yellow-100 text-yellow-700",
    high: "bg-orange-100 text-orange-700",
    critical: "bg-red-100 text-red-700",
  }
  const LABELS: Record<string, string> = {
    low: "低",
    medium: "中",
    high: "高",
    critical: "极高",
  }
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${MAP[level] ?? "bg-stone-100 text-stone-600"}`}
    >
      {LABELS[level] ?? level}
    </span>
  )
}

function PriorityBadge({ priority }: { priority: string }) {
  const MAP: Record<string, string> = {
    critical: "bg-red-100 text-red-700",
    immediate: "bg-red-100 text-red-700",
    high: "bg-orange-100 text-orange-700",
    short_term: "bg-orange-100 text-orange-700",
    medium: "bg-yellow-100 text-yellow-700",
    low: "bg-green-100 text-green-700",
    ongoing: "bg-blue-100 text-blue-700",
  }
  const LABELS: Record<string, string> = {
    critical: "紧急",
    immediate: "立即",
    high: "高",
    short_term: "近期",
    medium: "中",
    low: "低",
    ongoing: "持续",
  }
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${MAP[priority] ?? "bg-stone-100 text-stone-600"}`}
    >
      {LABELS[priority] ?? priority}
    </span>
  )
}

function Section({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="mb-4">
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
        {title}
      </h4>
      {children}
    </div>
  )
}

function BulletList({ items }: { items: string[] }) {
  if (!items.length) return null
  return (
    <ul className="space-y-1 pl-3">
      {items.map((item, i) => (
        <li key={i} className="flex gap-2 text-sm text-slate-700">
          <span className="shrink-0 text-slate-400">·</span>
          <span>{stripMd(item)}</span>
        </li>
      ))}
    </ul>
  )
}

// ── Qualification ─────────────────────────────────────────────────────────────
const CAT_LABELS: Record<string, string> = {
  Legal: "法律资质",
  Financial: "财务要求",
  Technical: "技术能力",
  Experience: "项目经验",
}

function QualificationView({ data }: { data: Rec }) {
  const reqs = arr(data.qualification_requirements) as Rec[]
  const implied = arr(data.implied_requirements) as Rec[]
  const jv = rec(data.joint_venture_requirements)
  const domestic = rec(data.domestic_preference)
  const summary = rec(data.qualification_summary)

  return (
    <div className="space-y-3 pt-1">
      {num(summary.total_requirements) > 0 && (
        <div className="flex flex-wrap gap-2 pb-1">
          <span className="rounded bg-slate-100 px-2 py-1 text-xs text-slate-600">
            共 {num(summary.total_requirements)} 项要求
          </span>
          {num(summary.pass_fail_count) > 0 && (
            <span className="rounded bg-red-50 px-2 py-1 text-xs text-red-600">
              {num(summary.pass_fail_count)} 项硬性 (Pass/Fail)
            </span>
          )}
          {num(summary.scoring_count) > 0 && (
            <span className="rounded bg-blue-50 px-2 py-1 text-xs text-blue-600">
              {num(summary.scoring_count)} 项评分
            </span>
          )}
        </div>
      )}
      {reqs.map((req, i) => (
        <div key={i} className="rounded-lg border border-slate-100 bg-slate-50 p-3">
          <div className="mb-2 flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-700">
              {CAT_LABELS[str(req.category)] ?? str(req.category)}
            </span>
            {str(req.type) && (
              <span className={`rounded px-1.5 py-0.5 text-xs ${str(req.type) === "pass_fail" ? "bg-red-50 text-red-600" : "bg-blue-50 text-blue-600"}`}>
                {str(req.type) === "pass_fail" ? "Pass/Fail" : "评分"}
              </span>
            )}
            {str(req.source_reference) && (
              <span className="text-xs text-slate-400">{str(req.source_reference)}</span>
            )}
          </div>
          <p className="mb-1 text-sm text-slate-800">{str(req.requirement)}</p>
          {/* Backward compat: old format used requirements array */}
          <BulletList items={arr(req.requirements) as string[]} />
          {(arr(req.evidence_required) as string[]).length > 0 ? (
            <div className="mt-2 border-t border-slate-200 pt-2">
              <p className="mb-1 text-xs text-slate-400">所需证明文件</p>
              <BulletList items={arr(req.evidence_required) as string[]} />
            </div>
          ) : null}
          {rec(req.self_check).question ? (
            <div className="mt-2 rounded bg-amber-50 px-2 py-1.5 text-xs text-amber-700">
              ☐ {str(rec(req.self_check).question)}
              {str(rec(req.self_check).guidance) && (
                <span className="block mt-0.5 text-amber-600">{str(rec(req.self_check).guidance)}</span>
              )}
            </div>
          ) : null}
        </div>
      ))}
      {implied.length > 0 && (
        <Section title="隐含要求">
          {implied.map((imp, i) => (
            <div key={i} className="mb-2 rounded-lg border border-amber-100 bg-amber-50 p-3">
              <p className="text-sm text-amber-800">{str(imp.requirement)}</p>
              <p className="mt-1 text-xs text-amber-600">推断依据：{str(imp.basis)}</p>
              {str(imp.recommendation) && (
                <p className="mt-1 text-xs text-amber-700">→ {str(imp.recommendation)}</p>
              )}
            </div>
          ))}
        </Section>
      )}
      {(jv.allowed !== undefined || domestic.applicable !== undefined) && (
        <div className="flex flex-wrap gap-2 pt-1">
          {jv.allowed !== undefined && (
            <span className="rounded bg-slate-100 px-2 py-1 text-xs text-slate-600">
              联合体：
              {bool(jv.allowed)
                ? `允许（最多 ${num(jv.max_members)} 方，主方 ≥ ${str(jv.lead_partner_min_share)}）`
                : "不允许"}
            </span>
          )}
          {domestic.applicable !== undefined && (
            <span className="rounded bg-slate-100 px-2 py-1 text-xs text-slate-600">
              国内优惠：{bool(domestic.applicable) ? `适用（${str(domestic.margin)}）` : "不适用"}
            </span>
          )}
        </div>
      )}
    </div>
  )
}

// ── Evaluation ────────────────────────────────────────────────────────────────
function EvaluationView({ data }: { data: Rec }) {
  const evalMethodObj = rec(data.evaluation_method)
  const method = str(evalMethodObj.type) || str(data.evaluation_method)
  const tw = num(data.technical_weight)
  const fw = num(data.financial_weight)
  const criteria = arr(data.technical_criteria) as Rec[]
  const thresholds = rec(data.qualification_thresholds)
  const finEval = rec(data.financial_evaluation)
  const scoringTips = arr(data.scoring_tips) as string[]

  return (
    <div className="space-y-4 pt-1">
      <div className="flex flex-wrap items-center gap-3">
        {method && (
          <Badge className="border-transparent bg-blue-100 text-blue-700">{method}</Badge>
        )}
        {tw > 0 && (
          <span className="text-sm text-slate-600">
            技术 <strong>{tw}%</strong> ／ 财务 <strong>{fw}%</strong>
          </span>
        )}
        {thresholds.technical_minimum !== undefined && (
          <span className="rounded border border-amber-200 bg-amber-50 px-2 py-0.5 text-xs text-amber-700">
            技术最低通过分：{num(thresholds.technical_minimum)}
          </span>
        )}
      </div>
      {(str(evalMethodObj.introduction) || str(evalMethodObj.guidance_notes)) && (
        <div className="rounded-lg border border-blue-100 bg-blue-50 p-3 space-y-1">
          {str(evalMethodObj.introduction) && (
            <p className="text-sm text-blue-800">{str(evalMethodObj.introduction)}</p>
          )}
          {str(evalMethodObj.guidance_notes) && (
            <p className="text-xs text-blue-700">💡 {str(evalMethodObj.guidance_notes)}</p>
          )}
        </div>
      )}
      {criteria.length > 0 && (
        <Section title="评分标准">
          <div className="space-y-2">
            {criteria.map((c, i) => (
              <div key={i} className="rounded-lg border border-slate-100 bg-slate-50 p-3">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-800">{str(c.criterion)}</span>
                  <span className="rounded bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-600">
                    权重 {num(c.weight)}%
                  </span>
                </div>
                {(arr(c.sub_criteria) as Rec[]).length > 0 && (
                  <div className="space-y-1 border-l-2 border-slate-200 pl-2">
                    {(arr(c.sub_criteria) as Rec[]).map((s, j) => (
                      <div key={j} className="flex justify-between">
                        <span className="text-xs text-slate-600">{str(s.name)}</span>
                        <span className="text-xs text-slate-500">{num(s.max_score)} 分</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}
      {scoringTips.length > 0 && (
        <Section title="评分策略提示">
          <div className="space-y-1">
            {scoringTips.map((tip, i) => (
              <p key={i} className="rounded bg-green-50 px-2 py-1 text-xs text-green-700">
                💡 {tip}
              </p>
            ))}
          </div>
        </Section>
      )}
      {str(finEval.formula) && (
        <Section title="财务评分公式">
          <p className="rounded bg-slate-50 px-3 py-2 font-mono text-sm text-slate-700">
            {str(finEval.formula)}
          </p>
          {str(finEval.description) && (
            <p className="mt-1 text-xs text-slate-500">{str(finEval.description)}</p>
          )}
        </Section>
      )}
    </div>
  )
}

// ── Key Dates ─────────────────────────────────────────────────────────────────
const DATE_LABEL: Record<string, string> = {
  submission_deadline: "提交截止",
  clarification_deadline: "澄清截止",
  pre_bid_meeting: "标前会议",
  site_visit: "现场踏勘",
  evaluation_period: "评标期",
  contract_start: "合同开始",
}
const DATE_COLOR: Record<string, string> = {
  submission_deadline: "bg-red-100 text-red-700",
  clarification_deadline: "bg-orange-100 text-orange-700",
  pre_bid_meeting: "bg-blue-100 text-blue-700",
  site_visit: "bg-teal-100 text-teal-700",
  evaluation_period: "bg-purple-100 text-purple-700",
  contract_start: "bg-green-100 text-green-700",
}

function KeyDatesView({ data }: { data: Rec }) {
  const dates = arr(data.key_dates) as Rec[]
  const summary = rec(data.timeline_summary)
  const warnings = arr(data.warnings) as string[]
  const urgency = rec(data.urgency_assessment)
  const rhythm = arr(data.preparation_rhythm) as Rec[]

  const urgencyLevel = str(urgency.level)
  const urgencyStyle = urgencyLevel === "red"
    ? "border-red-200 bg-red-50 text-red-800"
    : urgencyLevel === "yellow"
      ? "border-amber-200 bg-amber-50 text-amber-800"
      : urgencyLevel === "green"
        ? "border-green-200 bg-green-50 text-green-800"
        : ""

  return (
    <div className="space-y-4 pt-1">
      {urgencyLevel && (
        <div className={`rounded-lg border p-3 ${urgencyStyle}`}>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-semibold">
              {urgencyLevel === "red" ? "🔴 紧急" : urgencyLevel === "yellow" ? "🟡 注意时间" : "🟢 时间充裕"}
            </span>
          </div>
          <p className="text-sm">{str(urgency.description)}</p>
          {str(urgency.rationale) && (
            <p className="mt-1 text-xs opacity-80">{str(urgency.rationale)}</p>
          )}
        </div>
      )}
      {warnings.length > 0 && (
        <div className="space-y-1 rounded-lg border border-amber-200 bg-amber-50 p-3">
          {warnings.map((w, i) => (
            <p key={i} className="flex gap-2 text-sm text-amber-800">
              <span>⚠️</span>
              <span>{stripMd(w)}</span>
            </p>
          ))}
        </div>
      )}
      <div className="space-y-0.5">
        {dates.map((d, i) => {
          const cat = str(d.category)
          return (
            <div
              key={i}
              className="flex items-start gap-3 border-b border-slate-100 py-2 last:border-0"
            >
              <span
                className={`mt-0.5 shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold ${DATE_COLOR[cat] ?? "bg-slate-100 text-slate-600"}`}
              >
                {DATE_LABEL[cat] ?? cat}
              </span>
              <div className="flex-1">
                <p className="text-sm text-slate-800">{str(d.event)}</p>
                {str(d.time_zone) && (
                  <p className="text-xs text-slate-400">{str(d.time_zone)}</p>
                )}
              </div>
              <div className="flex shrink-0 flex-col items-end">
                <span className="text-sm font-semibold text-slate-700">
                  {str(d.date)}
                </span>
                {d.days_from_today !== undefined && d.days_from_today !== null && (
                  <span className={`text-xs ${num(d.days_from_today) < 0 ? "text-slate-400" : num(d.days_from_today) <= 7 ? "text-red-500 font-semibold" : "text-slate-500"}`}>
                    {num(d.days_from_today) < 0 ? `已过 ${Math.abs(num(d.days_from_today))} 天` : `还剩 ${num(d.days_from_today)} 天`}
                  </span>
                )}
              </div>
            </div>
          )
        })}
      </div>
      {Object.values(summary).some(Boolean) && (
        <div className="grid grid-cols-2 gap-2 pt-1 sm:grid-cols-3">
          {summary.remaining_days_to_submission !== undefined && summary.remaining_days_to_submission !== null && (
            <div className="rounded bg-slate-50 p-2 text-center">
              <p className="text-2xl font-bold text-slate-800">
                {num(summary.remaining_days_to_submission)}
              </p>
              <p className="text-xs text-slate-500">距截标剩余天数</p>
            </div>
          )}
          {summary.total_days_from_issue_to_submission !== undefined && (
            <div className="rounded bg-slate-50 p-2 text-center">
              <p className="text-2xl font-bold text-slate-800">
                {num(summary.total_days_from_issue_to_submission)}
              </p>
              <p className="text-xs text-slate-500">发布至截标天数</p>
            </div>
          )}
          {summary.clarification_cutoff_before_deadline_days !== undefined && (
            <div className="rounded bg-slate-50 p-2 text-center">
              <p className="text-2xl font-bold text-slate-800">
                {num(summary.clarification_cutoff_before_deadline_days)}
              </p>
              <p className="text-xs text-slate-500">澄清截止提前天数</p>
            </div>
          )}
        </div>
      )}
      {rhythm.length > 0 && (
        <Section title="准备节奏建议">
          <div className="space-y-2">
            {rhythm.map((r, i) => (
              <div key={i} className="flex items-start gap-3 rounded-lg border border-slate-100 bg-slate-50 p-3">
                <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-700">
                  {i + 1}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-800">{str(r.milestone)}</span>
                    {str(r.suggested_date) && (
                      <span className="text-xs text-slate-500">{str(r.suggested_date)}</span>
                    )}
                    {num(r.days_before_deadline) > 0 && (
                      <span className="text-xs text-slate-400">截标前 {num(r.days_before_deadline)} 天</span>
                    )}
                  </div>
                  <BulletList items={arr(r.key_tasks) as string[]} />
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  )
}

// ── Submission ────────────────────────────────────────────────────────────────
function SubmissionView({ data }: { data: Rec }) {
  const format = rec(data.submission_format)
  const copies = rec(data.copies)
  const language = rec(data.language)
  const security = rec(data.bid_security)
  const docs = arr(data.required_documents) as Rec[]

  const methodLabel =
    str(format.method) === "online"
      ? "线上"
      : str(format.method) === "physical"
        ? "纸质"
        : str(format.method) === "both"
          ? "线上 + 纸质"
          : str(format.method)

  return (
    <div className="space-y-4 pt-1">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {str(format.method) && (
          <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
            <p className="mb-1 text-xs text-slate-500">提交方式</p>
            <p className="text-sm font-medium text-slate-800">{methodLabel}</p>
            {str(format.online_platform) && (
              <p className="mt-0.5 truncate text-xs text-slate-500">
                {str(format.online_platform)}
              </p>
            )}
          </div>
        )}
        {copies.original !== undefined && (
          <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
            <p className="mb-1 text-xs text-slate-500">份数要求</p>
            <p className="text-sm font-medium text-slate-800">
              原件 {num(copies.original)} 份
              {num(copies.copies) > 0 ? `，副本 ${num(copies.copies)} 份` : ""}
              {num(copies.electronic_copies) > 0
                ? `，电子 ${num(copies.electronic_copies)} 份`
                : ""}
            </p>
            {str(copies.format_requirements) && (
              <p className="mt-0.5 text-xs text-slate-500">
                {str(copies.format_requirements)}
              </p>
            )}
          </div>
        )}
        {str(language.primary) && (
          <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
            <p className="mb-1 text-xs text-slate-500">语言</p>
            <p className="text-sm font-medium text-slate-800">{str(language.primary)}</p>
            {bool(language.certified_translation) && (
              <p className="mt-0.5 text-xs text-amber-600">需认证翻译</p>
            )}
          </div>
        )}
      </div>
      {bool(security.required) && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
          <p className="mb-1 text-xs font-semibold text-amber-700">💰 投标保证金</p>
          <p className="text-sm text-amber-800">
            {str(security.amount)} {str(security.currency)}，形式：{str(security.form)}
            {num(security.validity_days) > 0 ? `，有效期 ${num(security.validity_days)} 天` : ""}
          </p>
        </div>
      )}
      {docs.length > 0 && (
        <Section title={`必交文件（${docs.length} 项）`}>
          <div className="space-y-1.5">
            {docs.map((d, i) => (
              <div
                key={i}
                className="flex items-start gap-2 border-b border-slate-100 py-1.5 last:border-0"
              >
                <span
                  className={`shrink-0 rounded px-1.5 py-0.5 text-xs font-medium ${bool(d.mandatory) ? "bg-red-50 text-red-600" : "bg-slate-100 text-slate-500"}`}
                >
                  {bool(d.mandatory) ? "必交" : "可选"}
                </span>
                <div>
                  <p className="text-sm text-slate-800">{str(d.document)}</p>
                  {str(d.notes) && <p className="text-xs text-slate-500">{str(d.notes)}</p>}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  )
}

// ── BDS Modifications ─────────────────────────────────────────────────────────
const PRIORITY_ORDER: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
}

function BDSView({ data }: { data: Rec }) {
  const mods = arr(data.bds_modifications) as Rec[]
  const summary = str(data.critical_changes_summary)
  const checklist = arr(data.compliance_checklist) as Rec[]
  const stats = rec(data.statistics)
  const sorted = [...mods].sort(
    (a, b) => (PRIORITY_ORDER[str(a.priority)] ?? 9) - (PRIORITY_ORDER[str(b.priority)] ?? 9),
  )

  return (
    <div className="space-y-4 pt-1">
      {num(stats.total_bds_items) > 0 && (
        <div className="flex flex-wrap gap-2">
          <span className="rounded bg-slate-100 px-2 py-1 text-xs text-slate-600">
            共 {num(stats.total_bds_items)} 条
          </span>
          {num(stats.critical_count) > 0 && (
            <span className="rounded bg-red-50 px-2 py-1 text-xs text-red-600">
              {num(stats.critical_count)} 关键
            </span>
          )}
          {num(stats.high_count) > 0 && (
            <span className="rounded bg-orange-50 px-2 py-1 text-xs text-orange-600">
              {num(stats.high_count)} 高优先
            </span>
          )}
        </div>
      )}
      {summary && (
        <div className="rounded-lg border border-slate-100 bg-slate-50 p-3 text-sm text-slate-700">
          {summary}
        </div>
      )}
      {sorted.length > 0 && (
        <div className="space-y-2">
          {sorted.map((mod, i) => (
            <div key={i} className="rounded-lg border border-slate-100 p-3">
              <div className="mb-1.5 flex items-center gap-2">
                <PriorityBadge priority={str(mod.priority)} />
                <span className="font-mono text-xs text-slate-500">{str(mod.itb_clause)}</span>
                {str(mod.bds_reference) && (
                  <span className="text-xs text-slate-400">{str(mod.bds_reference)}</span>
                )}
                {str(mod.change_type) && (
                  <span className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-500">
                    {str(mod.change_type)}
                  </span>
                )}
              </div>
              {str(mod.itb_standard_content) && (
                <div className="mb-1.5 rounded bg-blue-50 px-2 py-1">
                  <p className="text-xs text-blue-600">
                    <span className="font-semibold">ITB 标准：</span>
                    {str(mod.itb_standard_content)}
                  </p>
                </div>
              )}
              <p className="mb-1 text-sm text-slate-800">
                {str(mod.bds_modification) || str(mod.modification)}
              </p>
              {str(mod.impact_analysis) && (
                <p className="mb-1 text-xs text-slate-600">
                  影响：{str(mod.impact_analysis)}
                </p>
              )}
              {str(mod.action_required) && (
                <p className="rounded bg-blue-50 px-2 py-1 text-xs text-blue-700">
                  → {str(mod.action_required)}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
      {checklist.length > 0 && (
        <Section title="合规清单">
          <div className="space-y-1">
            {checklist.map((item, i) => (
              <div key={i} className="flex items-start gap-2 text-sm text-slate-700">
                <span className="shrink-0 text-green-500">☐</span>
                <span>{str(item.item)}</span>
                {str(item.bds_reference) && (
                  <span className="shrink-0 text-xs text-slate-400">{str(item.bds_reference)}</span>
                )}
                {str(item.difficulty) && (
                  <span className={`shrink-0 rounded px-1.5 py-0.5 text-xs ${str(item.difficulty) === "challenging" ? "bg-red-50 text-red-600" : str(item.difficulty) === "moderate" ? "bg-amber-50 text-amber-600" : "bg-green-50 text-green-600"}`}>
                    {str(item.difficulty) === "challenging" ? "困难" : str(item.difficulty) === "moderate" ? "中等" : "简单"}
                  </span>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  )
}

// ── Methodology ───────────────────────────────────────────────────────────────
function MethodologyView({ data }: { data: Rec }) {
  const evalMethod = rec(data.evaluation_method)
  const criteria = arr(data.scoring_criteria) as Rec[]
  const thresholds = rec(data.critical_thresholds)
  const strategy = rec(data.win_strategy)

  return (
    <div className="space-y-4 pt-1">
      <div className="flex flex-wrap items-center gap-3">
        {str(evalMethod.type) && (
          <Badge className="border-transparent bg-blue-100 text-blue-700">
            {str(evalMethod.type)}
            {evalMethod.full_name ? ` — ${str(evalMethod.full_name)}` : ""}
          </Badge>
        )}
        {evalMethod.minimum_technical_score !== undefined && (
          <span className="rounded border border-amber-200 bg-amber-50 px-2 py-0.5 text-xs text-amber-700">
            技术最低通过分：{num(evalMethod.minimum_technical_score)}
          </span>
        )}
      </div>
      {criteria.length > 0 && (
        <Section title="评分体系">
          <div className="space-y-3">
            {criteria.map((c, i) => (
              <div key={i} className="rounded-lg border border-slate-100 bg-slate-50 p-3">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-sm font-medium">{str(c.category)}</span>
                  <span className="text-xs font-semibold text-blue-600">权重 {num(c.weight)}%</span>
                </div>
                {(arr(c.sub_criteria) as Rec[]).length > 0 && (
                  <div className="mb-2 space-y-1 border-l-2 border-slate-200 pl-2">
                    {(arr(c.sub_criteria) as Rec[]).map((s, j) => (
                      <div key={j} className="flex justify-between">
                        <span className="text-xs text-slate-600">{str(s.name)}</span>
                        <span className="text-xs text-slate-500">{num(s.max_score)} 分</span>
                      </div>
                    ))}
                  </div>
                )}
                {str(c.strategy_tips) && (
                  <p className="rounded bg-green-50 px-2 py-1 text-xs text-green-700">
                    💡 {str(c.strategy_tips)}
                  </p>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}
      {str(strategy.overall_recommendation) && (
        <Section title="总体制胜策略">
          <p className="rounded-lg bg-green-50 p-3 text-sm text-slate-700">
            {str(strategy.overall_recommendation)}
          </p>
        </Section>
      )}
      {str(thresholds.financial_formula) && (
        <Section title="评分公式">
          <p className="rounded border border-slate-100 bg-slate-50 px-3 py-2 font-mono text-sm">
            {str(thresholds.financial_formula)}
          </p>
          {str(thresholds.combined_formula) && (
            <p className="mt-1 rounded border border-slate-100 bg-slate-50 px-3 py-2 font-mono text-sm">
              {str(thresholds.combined_formula)}
            </p>
          )}
        </Section>
      )}
    </div>
  )
}

// ── Commercial ────────────────────────────────────────────────────────────────
const GUARANTEE_LABEL: Record<string, string> = {
  performance: "履约保证金",
  advance_payment: "预付款保函",
  bid_security: "投标保证金",
}

function CommercialView({ data }: { data: Rec }) {
  const payment = rec(data.payment_terms)
  const schedule = arr(payment.payment_schedule) as Rec[]
  const advance = rec(payment.advance_payment)
  const retention = rec(payment.retention)
  const guarantees = arr(data.guarantees) as Rec[]
  const warranty = rec(data.warranty)
  const penalties = rec(data.penalties)
  const ld = rec(penalties.liquidated_damages)

  return (
    <div className="space-y-4 pt-1">
      {schedule.length > 0 && (
        <Section title="支付计划">
          <div className="space-y-1">
            {schedule.map((s, i) => (
              <div
                key={i}
                className="flex items-center gap-3 border-b border-slate-100 py-1.5 last:border-0"
              >
                <span className="w-12 shrink-0 text-right text-lg font-bold text-blue-600">
                  {num(s.percentage)}%
                </span>
                <div>
                  <p className="text-sm font-medium text-slate-800">{str(s.milestone)}</p>
                  {str(s.condition) && (
                    <p className="text-xs text-slate-500">{str(s.condition)}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
          {bool(advance.available) && (
            <div className="mt-2 rounded bg-blue-50 px-3 py-2 text-xs text-blue-700">
              预付款：{num(advance.percentage)}%
              {bool(advance.guarantee_required) ? "（需提供预付款保函）" : ""}
            </div>
          )}
          {retention.percentage !== undefined && (
            <div className="mt-1 rounded bg-amber-50 px-3 py-2 text-xs text-amber-700">
              质保扣款：{num(retention.percentage)}%，释放条件：{str(retention.release_condition)}
            </div>
          )}
        </Section>
      )}
      {guarantees.length > 0 && (
        <Section title="保证金 / 担保">
          <div className="space-y-1.5">
            {guarantees.map((g, i) => (
              <div
                key={i}
                className="flex items-center gap-3 rounded border border-slate-100 bg-slate-50 px-3 py-2"
              >
                <span className="w-24 shrink-0 text-xs font-semibold text-slate-600">
                  {GUARANTEE_LABEL[str(g.type)] ?? str(g.type)}
                </span>
                <span className="text-sm text-slate-800">{num(g.percentage)}%</span>
                <span className="text-xs text-slate-500">有效期：{str(g.validity)}</span>
                <span className="text-xs text-slate-400">{str(g.form)}</span>
              </div>
            ))}
          </div>
        </Section>
      )}
      {(warranty.period_months !== undefined || str(ld.rate)) && (
        <Section title="违约 & 保修">
          {warranty.period_months !== undefined && (
            <p className="mb-1 text-sm text-slate-700">
              质保期：<strong>{num(warranty.period_months)} 个月</strong>
              {warranty.scope ? `，覆盖：${str(warranty.scope)}` : ""}
            </p>
          )}
          {str(ld.rate) && (
            <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">
              违约金：{str(ld.rate)}，上限 {str(ld.cap)}，适用于 {str(ld.applicable_for)}
            </p>
          )}
        </Section>
      )}
    </div>
  )
}

// ── Risk Assessment ───────────────────────────────────────────────────────────
const RISK_DIM_LABEL: Record<string, string> = {
  qualification: "资质",
  technical: "技术",
  financial: "财务",
  timeline: "时间",
  compliance: "合规",
}

const DECISION_STYLE: Record<
  string,
  { label: string; cls: string; border: string }
> = {
  bid: {
    label: "建议投标 ✅",
    cls: "text-green-700",
    border: "border-green-300 bg-green-50",
  },
  conditional_bid: {
    label: "有条件投标 ⚠️",
    cls: "text-amber-700",
    border: "border-amber-300 bg-amber-50",
  },
  no_bid: {
    label: "不建议投标 ❌",
    cls: "text-red-700",
    border: "border-red-300 bg-red-50",
  },
}

function RiskView({ data }: { data: Rec }) {
  const recommend = rec(data.bid_recommendation)
  const decision = str(recommend.decision)
  const rationale = str(recommend.rationale)
  const strengths = arr(recommend.key_strengths) as string[]
  const weaknesses = arr(recommend.key_weaknesses) as string[]
  const conditions = arr(recommend.conditions) as string[]
  const dimensions = arr(data.risk_dimensions) as Rec[]
  const actionItems = arr(data.action_items) as Rec[]
  const dStyle = DECISION_STYLE[decision] ?? {
    label: decision,
    cls: "text-slate-700",
    border: "border-slate-200 bg-slate-50",
  }

  return (
    <div className="space-y-5 pt-1">
      {/* Decision card */}
      {decision && (
        <div className={`rounded-xl border-2 p-4 ${dStyle.border}`}>
          <div className="mb-2">
            <h3 className={`text-xl font-bold ${dStyle.cls}`}>{dStyle.label}</h3>
          </div>
          {rationale && <p className="mb-3 text-sm text-slate-700">{rationale}</p>}
          {conditions.length > 0 && (
            <div className="mb-3">
              <p className="mb-1 text-xs font-semibold text-amber-700">投标条件</p>
              <BulletList items={conditions} />
            </div>
          )}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {strengths.length > 0 && (
              <div className="rounded-lg bg-white/60 p-3">
                <p className="mb-1 text-xs font-semibold text-green-700">优势</p>
                <BulletList items={strengths} />
              </div>
            )}
            {weaknesses.length > 0 && (
              <div className="rounded-lg bg-white/60 p-3">
                <p className="mb-1 text-xs font-semibold text-red-700">劣势</p>
                <BulletList items={weaknesses} />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Risk dimensions */}
      {dimensions.length > 0 && (
        <Section title="风险维度">
          <div className="space-y-2">
            {dimensions.map((d, i) => (
              <div key={i} className="rounded-lg border border-slate-100 p-3">
                <div className="mb-2 flex items-center gap-3">
                  <span className="w-10 shrink-0 text-sm font-medium text-slate-700">
                    {RISK_DIM_LABEL[str(d.dimension)] ?? str(d.dimension)}
                  </span>
                  <RiskBadge level={str(d.risk_level)} />
                  {num(d.score) > 0 && (
                    <span className="ml-auto text-xs text-slate-500">得分 {num(d.score)}</span>
                  )}
                </div>
                {(arr(d.factors) as Rec[]).length > 0 && (
                  <div className="space-y-1 pl-2">
                    {(arr(d.factors) as Rec[]).slice(0, 3).map((f, j) => (
                      <p key={j} className="text-xs text-slate-600">
                        <span className="font-medium">{str(f.factor)}</span>
                        {str(f.mitigation) && (
                          <span className="text-slate-400"> → {str(f.mitigation)}</span>
                        )}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Action items */}
      {actionItems.length > 0 && (
        <Section title="行动清单">
          <div className="space-y-2">
            {actionItems.map((item, i) => (
              <div
                key={i}
                className="flex items-start gap-3 rounded-lg border border-slate-100 p-3"
              >
                <PriorityBadge priority={str(item.priority)} />
                <div className="flex-1">
                  <p className="text-sm text-slate-800">{str(item.action)}</p>
                  <div className="mt-0.5 flex gap-3">
                    {str(item.responsible) && (
                      <span className="text-xs text-slate-500">负责：{str(item.responsible)}</span>
                    )}
                    {str(item.deadline) && (
                      <span className="text-xs text-slate-500">截止：{str(item.deadline)}</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  )
}

// ── Executive Summary ─────────────────────────────────────────────────────────
function ExecutiveSummaryView({ data }: { data: Rec }) {
  const procurement = rec(data.procurement_method)
  const lot = rec(data.lot_info)
  const assessment = rec(data.quick_assessment)

  const attractivenessStyle = str(assessment.attractiveness) === "high"
    ? "border-green-200 bg-green-50 text-green-800"
    : str(assessment.attractiveness) === "medium"
      ? "border-amber-200 bg-amber-50 text-amber-800"
      : str(assessment.attractiveness) === "low"
        ? "border-red-200 bg-red-50 text-red-800"
        : "border-slate-200 bg-slate-50 text-slate-800"

  return (
    <div className="space-y-4 pt-1">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {str(data.project_name) && (
          <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
            <p className="mb-1 text-xs text-slate-500">项目名称</p>
            <p className="text-sm font-medium text-slate-800">{str(data.project_name)}</p>
          </div>
        )}
        {str(data.country_region) && (
          <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
            <p className="mb-1 text-xs text-slate-500">国家/地区</p>
            <p className="text-sm font-medium text-slate-800">{str(data.country_region)}</p>
          </div>
        )}
        {str(data.borrower_agency) && (
          <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
            <p className="mb-1 text-xs text-slate-500">采购机构</p>
            <p className="text-sm font-medium text-slate-800">{str(data.borrower_agency)}</p>
          </div>
        )}
        {str(data.funding_source) && (
          <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
            <p className="mb-1 text-xs text-slate-500">资金来源</p>
            <p className="text-sm font-medium text-slate-800">{str(data.funding_source)}</p>
          </div>
        )}
        {str(data.estimated_budget) && (
          <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
            <p className="mb-1 text-xs text-slate-500">预估预算</p>
            <p className="text-sm font-medium text-slate-800">{str(data.estimated_budget)}</p>
          </div>
        )}
        {str(procurement.type) && (
          <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
            <p className="mb-1 text-xs text-slate-500">采购方式</p>
            <p className="text-sm font-medium text-slate-800">
              {str(procurement.type)} — {str(procurement.full_name)}
            </p>
            {str(procurement.brief_description) && (
              <p className="mt-0.5 text-xs text-slate-500">{str(procurement.brief_description)}</p>
            )}
          </div>
        )}
        {str(data.contract_type) && (
          <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
            <p className="mb-1 text-xs text-slate-500">合同类型</p>
            <p className="text-sm font-medium text-slate-800">{str(data.contract_type)}</p>
          </div>
        )}
        {str(data.industry_sector) && (
          <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
            <p className="mb-1 text-xs text-slate-500">行业领域</p>
            <p className="text-sm font-medium text-slate-800">{str(data.industry_sector)}</p>
          </div>
        )}
      </div>
      {bool(lot.has_lots) && (
        <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
          <p className="mb-1 text-xs text-slate-500">标段信息（{num(lot.lot_count)} 个标段）</p>
          <BulletList items={arr(lot.lot_descriptions) as string[]} />
        </div>
      )}
      {str(data.project_scope_summary) && (
        <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
          <p className="mb-1 text-xs text-slate-500">项目范围</p>
          <p className="text-sm text-slate-800">{str(data.project_scope_summary)}</p>
        </div>
      )}
      {str(assessment.attractiveness) && (
        <div className={`rounded-lg border p-3 ${attractivenessStyle}`}>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-semibold">
              快速评估：{str(assessment.attractiveness) === "high" ? "值得投标 ✅" : str(assessment.attractiveness) === "medium" ? "需进一步分析 ⚠️" : "谨慎考虑 ❌"}
            </span>
          </div>
          {str(assessment.rationale) && (
            <p className="text-sm">{str(assessment.rationale)}</p>
          )}
          {(arr(assessment.key_considerations) as string[]).length > 0 && (
            <BulletList items={arr(assessment.key_considerations) as string[]} />
          )}
        </div>
      )}
    </div>
  )
}

// ── Technical Requirements ───────────────────────────────────────────────────
function TechnicalView({ data }: { data: Rec }) {
  const scope = rec(data.project_scope)
  const deliverables = arr(data.deliverables) as Rec[]
  const standards = arr(data.technical_standards) as Rec[]
  const personnel = arr(data.key_personnel) as Rec[]
  const risks = arr(data.risk_areas) as Rec[]
  const clarifications = arr(data.clarification_needed) as Rec[]

  return (
    <div className="space-y-4 pt-1">
      {(str(scope.objective) || str(scope.scope_summary)) && (
        <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
          {str(scope.objective) && (
            <p className="mb-1 text-sm font-medium text-slate-800">{str(scope.objective)}</p>
          )}
          {str(scope.scope_summary) && (
            <p className="text-sm text-slate-700">{str(scope.scope_summary)}</p>
          )}
          <div className="mt-2 flex flex-wrap gap-2">
            {str(scope.geographic_coverage) && (
              <span className="rounded bg-blue-50 px-2 py-0.5 text-xs text-blue-600">📍 {str(scope.geographic_coverage)}</span>
            )}
            {str(scope.implementation_period) && (
              <span className="rounded bg-blue-50 px-2 py-0.5 text-xs text-blue-600">⏱ {str(scope.implementation_period)}</span>
            )}
          </div>
        </div>
      )}
      {deliverables.length > 0 && (
        <Section title={`交付物（${deliverables.length} 项）`}>
          <div className="space-y-2">
            {deliverables.map((d, i) => (
              <div key={i} className="rounded-lg border border-slate-100 bg-slate-50 p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-slate-800">{str(d.name)}</span>
                  {str(d.deadline) && (
                    <span className="text-xs text-slate-500">{str(d.deadline)}</span>
                  )}
                </div>
                {str(d.description) && (
                  <p className="text-xs text-slate-600">{str(d.description)}</p>
                )}
                {str(d.acceptance_criteria) && (
                  <p className="mt-1 text-xs text-green-700">验收标准：{str(d.acceptance_criteria)}</p>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}
      {personnel.length > 0 && (
        <Section title={`关键人员（${personnel.length} 个岗位）`}>
          <div className="space-y-2">
            {personnel.map((p, i) => (
              <div key={i} className="flex items-start gap-3 rounded-lg border border-slate-100 bg-slate-50 p-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-blue-700">
                  {i + 1}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-800">{str(p.position)}</p>
                  <p className="text-xs text-slate-600">{str(p.qualifications)}</p>
                  <div className="mt-1 flex flex-wrap gap-2">
                    {str(p.experience_years) && (
                      <span className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-500">经验 {str(p.experience_years)}</span>
                    )}
                    {str(p.man_months) && (
                      <span className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-500">{str(p.man_months)} 人月</span>
                    )}
                    {str(p.evaluation_weight) && (
                      <span className="rounded bg-amber-50 px-1.5 py-0.5 text-xs text-amber-600">权重 {str(p.evaluation_weight)}</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}
      {standards.length > 0 && (
        <Section title="技术标准">
          <div className="space-y-1">
            {standards.map((s, i) => (
              <div key={i} className="flex items-start gap-2 border-b border-slate-100 py-1.5 last:border-0">
                <span className="shrink-0 text-xs text-slate-400">📐</span>
                <div>
                  <p className="text-sm text-slate-800">{str(s.standard)}</p>
                  {str(s.description) && (
                    <p className="text-xs text-slate-500">{str(s.description)}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}
      {risks.length > 0 && (
        <Section title="技术风险">
          {risks.map((r, i) => (
            <div key={i} className="mb-2 rounded-lg border border-slate-100 p-3">
              <div className="flex items-center gap-2 mb-1">
                <RiskBadge level={str(r.impact)} />
                <span className="text-sm text-slate-800">{str(r.area)}</span>
              </div>
              <p className="text-xs text-slate-600">{str(r.description)}</p>
              {str(r.suggested_mitigation) && (
                <p className="mt-1 text-xs text-green-700">→ {str(r.suggested_mitigation)}</p>
              )}
            </div>
          ))}
        </Section>
      )}
      {clarifications.length > 0 && (
        <Section title="建议澄清事项">
          {clarifications.map((c, i) => (
            <div key={i} className="mb-2 rounded-lg border border-amber-100 bg-amber-50 p-3">
              <p className="text-sm text-amber-800">❓ {str(c.item)}</p>
              {str(c.reason) && (
                <p className="mt-0.5 text-xs text-amber-600">{str(c.reason)}</p>
              )}
              {str(c.suggested_question) && (
                <p className="mt-1 text-xs text-amber-700 italic">建议提问：{str(c.suggested_question)}</p>
              )}
            </div>
          ))}
        </Section>
      )}
    </div>
  )
}

// ── Technical Strategy ───────────────────────────────────────────────────────
function TechnicalStrategyView({ data }: { data: Rec }) {
  const framework = rec(data.proposal_framework)
  const structure = arr(framework.recommended_structure) as Rec[]
  const scoring = arr(data.scoring_strategy) as Rec[]
  const differentiators = arr(data.differentiators) as Rec[]
  const riskPlan = arr(data.risk_mitigation_plan) as Rec[]
  const themes = arr(data.win_themes) as string[]

  return (
    <div className="space-y-4 pt-1">
      {themes.length > 0 && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-3">
          <p className="mb-1 text-xs font-semibold text-green-700">🎯 核心中标主题</p>
          <BulletList items={themes} />
        </div>
      )}
      {str(framework.overall_approach) && (
        <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
          <p className="mb-1 text-xs text-slate-500">总体策略</p>
          <p className="text-sm text-slate-800">{str(framework.overall_approach)}</p>
        </div>
      )}
      {structure.length > 0 && (
        <Section title="技术方案建议结构">
          <div className="space-y-1.5">
            {structure.map((s, i) => (
              <div key={i} className="flex items-start gap-3 border-b border-slate-100 py-2 last:border-0">
                <span className={`shrink-0 rounded px-1.5 py-0.5 text-xs font-medium ${str(s.priority) === "high" ? "bg-red-50 text-red-600" : str(s.priority) === "medium" ? "bg-amber-50 text-amber-600" : "bg-green-50 text-green-600"}`}>
                  {str(s.priority) === "high" ? "★" : str(s.priority) === "medium" ? "●" : "○"}
                </span>
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-800">{str(s.section)}</p>
                  <p className="text-xs text-slate-600">{str(s.key_content)}</p>
                </div>
                {str(s.page_estimate) && (
                  <span className="shrink-0 text-xs text-slate-400">{str(s.page_estimate)} 页</span>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}
      {scoring.length > 0 && (
        <Section title="得分策略">
          <div className="space-y-2">
            {scoring.map((s, i) => (
              <div key={i} className="rounded-lg border border-slate-100 bg-slate-50 p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-slate-800">{str(s.criterion)}</span>
                  {num(s.weight) > 0 && (
                    <span className="rounded bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-600">
                      权重 {num(s.weight)}%
                    </span>
                  )}
                </div>
                {str(s.strategy) && (
                  <p className="mb-1 text-xs text-green-700">💡 {str(s.strategy)}</p>
                )}
                {(arr(s.key_evidence) as string[]).length > 0 && (
                  <div className="mt-1">
                    <p className="text-xs text-slate-500 mb-0.5">重点展示：</p>
                    <BulletList items={arr(s.key_evidence) as string[]} />
                  </div>
                )}
                {(arr(s.pitfalls) as string[]).length > 0 && (
                  <div className="mt-1">
                    <p className="text-xs text-red-500 mb-0.5">常见失分：</p>
                    <BulletList items={arr(s.pitfalls) as string[]} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}
      {differentiators.length > 0 && (
        <Section title="差异化竞争">
          {differentiators.map((d, i) => (
            <div key={i} className="mb-2 rounded-lg border border-slate-100 bg-slate-50 p-3">
              <p className="text-sm font-medium text-slate-800">{str(d.area)}</p>
              <p className="text-xs text-slate-600">{str(d.approach)}</p>
              {str(d.expected_impact) && (
                <p className="mt-1 text-xs text-green-700">预期影响：{str(d.expected_impact)}</p>
              )}
            </div>
          ))}
        </Section>
      )}
      {riskPlan.length > 0 && (
        <Section title="风险缓解方案">
          {riskPlan.map((r, i) => (
            <div key={i} className="mb-2 flex items-start gap-2 border-b border-slate-100 py-1.5 last:border-0">
              <span className={`shrink-0 rounded px-1.5 py-0.5 text-xs ${bool(r.include_in_proposal) ? "bg-green-50 text-green-600" : "bg-slate-100 text-slate-500"}`}>
                {bool(r.include_in_proposal) ? "写入方案" : "内部参考"}
              </span>
              <div>
                <p className="text-sm text-slate-800">{str(r.risk)}</p>
                <p className="text-xs text-slate-600">{str(r.mitigation_approach)}</p>
              </div>
            </div>
          ))}
        </Section>
      )}
    </div>
  )
}

// ── Compliance Matrix ────────────────────────────────────────────────────────
function ComplianceMatrixView({ data }: { data: Rec }) {
  const items = arr(data.compliance_items) as Rec[]
  const goNoGo = arr(data.go_no_go_checklist) as Rec[]
  const summary = rec(data.summary)

  const riskStyle = str(summary.overall_compliance_risk) === "high"
    ? "border-red-200 bg-red-50 text-red-800"
    : str(summary.overall_compliance_risk) === "medium"
      ? "border-amber-200 bg-amber-50 text-amber-800"
      : "border-green-200 bg-green-50 text-green-800"

  return (
    <div className="space-y-4 pt-1">
      {num(summary.total_mandatory) > 0 && (
        <div className={`rounded-lg border p-3 ${riskStyle}`}>
          <div className="flex flex-wrap gap-3 mb-1">
            <span className="text-sm font-semibold">
              合规风险：{str(summary.overall_compliance_risk) === "high" ? "🔴 高" : str(summary.overall_compliance_risk) === "medium" ? "🟡 中" : "🟢 低"}
            </span>
            <span className="text-xs">
              强制 {num(summary.total_mandatory)} 项 · 评分 {num(summary.total_scoring)} 项
            </span>
          </div>
          {(arr(summary.key_attention_areas) as string[]).length > 0 && (
            <BulletList items={arr(summary.key_attention_areas) as string[]} />
          )}
        </div>
      )}
      {goNoGo.length > 0 && (
        <Section title="Go/No-Go 检查">
          <div className="space-y-1.5">
            {goNoGo.map((item, i) => (
              <div key={i} className="flex items-start gap-2 rounded border border-slate-100 bg-slate-50 px-3 py-2">
                <span className={`shrink-0 text-sm ${bool(item.is_showstopper) ? "text-red-500" : "text-green-500"}`}>
                  {bool(item.is_showstopper) ? "🚫" : "☐"}
                </span>
                <div className="flex-1">
                  <p className="text-sm text-slate-800">{str(item.item)}</p>
                  {str(item.assessment_guidance) && (
                    <p className="text-xs text-slate-500">{str(item.assessment_guidance)}</p>
                  )}
                </div>
                {str(item.source_reference) && (
                  <span className="shrink-0 text-xs text-slate-400">{str(item.source_reference)}</span>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}
      {items.length > 0 && (
        <Section title={`合规检查项（${items.length} 项）`}>
          <div className="space-y-1.5">
            {items.map((item, i) => (
              <div key={i} className="flex items-start gap-2 border-b border-slate-100 py-2 last:border-0">
                <span className={`shrink-0 rounded px-1.5 py-0.5 text-xs font-medium ${str(item.type) === "mandatory" ? "bg-red-50 text-red-600" : str(item.type) === "scoring" ? "bg-blue-50 text-blue-600" : "bg-slate-100 text-slate-500"}`}>
                  {str(item.type) === "mandatory" ? "强制" : str(item.type) === "scoring" ? "评分" : "建议"}
                </span>
                <div className="flex-1">
                  <p className="text-sm text-slate-800">{str(item.requirement)}</p>
                  {str(item.action_required) && (
                    <p className="text-xs text-blue-700">→ {str(item.action_required)}</p>
                  )}
                  {str(item.evidence_needed) && (
                    <p className="text-xs text-slate-500">需提供：{str(item.evidence_needed)}</p>
                  )}
                </div>
                <div className="flex shrink-0 flex-col items-end gap-1">
                  {str(item.source) && (
                    <span className="text-xs text-slate-400">{str(item.source)} {str(item.reference)}</span>
                  )}
                  {str(item.difficulty) && (
                    <span className={`rounded px-1.5 py-0.5 text-xs ${str(item.difficulty) === "challenging" ? "bg-red-50 text-red-600" : str(item.difficulty) === "moderate" ? "bg-amber-50 text-amber-600" : "bg-green-50 text-green-600"}`}>
                      {str(item.difficulty) === "challenging" ? "困难" : str(item.difficulty) === "moderate" ? "中等" : "简单"}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  )
}

// ── Main dispatcher ───────────────────────────────────────────────────────────
interface AnalysisDimViewProps {
  dimension: string
  data: Record<string, unknown>
}

export function AnalysisDimView({ dimension, data }: AnalysisDimViewProps) {
  switch (dimension) {
    case "executive_summary":
      return <ExecutiveSummaryView data={data} />
    case "qualification":
      return <QualificationView data={data} />
    case "evaluation":
      return <EvaluationView data={data} />
    case "key_dates":
      return <KeyDatesView data={data} />
    case "submission":
      return <SubmissionView data={data} />
    case "bds_analysis":
      return <BDSView data={data} />
    case "technical_requirements":
      return <TechnicalView data={data} />
    case "methodology":
      return <MethodologyView data={data} />
    case "commercial":
      return <CommercialView data={data} />
    case "technical_strategy":
      return <TechnicalStrategyView data={data} />
    case "compliance_matrix":
      return <ComplianceMatrixView data={data} />
    case "risk_assessment":
      return <RiskView data={data} />
    default:
      return (
        <pre className="whitespace-pre-wrap text-xs text-slate-500">
          {JSON.stringify(data, null, 2)}
        </pre>
      )
  }
}
