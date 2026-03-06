"use client"

import { Badge } from "@/components/ui/badge"
import type React from "react"

// ── Type helpers ─────────────────────────────────────────────────────────────
type Rec = Record<string, unknown>
const str = (v: unknown): string => (typeof v === "string" ? v : "")
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
          <span>{item}</span>
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
  const jv = rec(data.joint_venture_requirements)
  const domestic = rec(data.domestic_preference)

  return (
    <div className="space-y-3 pt-1">
      {reqs.map((req, i) => (
        <div key={i} className="rounded-lg border border-slate-100 bg-slate-50 p-3">
          <div className="mb-2 flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-700">
              {CAT_LABELS[str(req.category)] ?? str(req.category)}
            </span>
            {str(req.source_reference) && (
              <span className="text-xs text-slate-400">{str(req.source_reference)}</span>
            )}
          </div>
          <BulletList items={arr(req.requirements) as string[]} />
          {(arr(req.evidence_required) as string[]).length > 0 && (
            <div className="mt-2 border-t border-slate-200 pt-2">
              <p className="mb-1 text-xs text-slate-400">所需证明文件</p>
              <BulletList items={arr(req.evidence_required) as string[]} />
            </div>
          )}
        </div>
      ))}
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
  const method = str(data.evaluation_method)
  const tw = num(data.technical_weight)
  const fw = num(data.financial_weight)
  const criteria = arr(data.technical_criteria) as Rec[]
  const thresholds = rec(data.qualification_thresholds)
  const finEval = rec(data.financial_evaluation)

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

  return (
    <div className="space-y-4 pt-1">
      {warnings.length > 0 && (
        <div className="space-y-1 rounded-lg border border-amber-200 bg-amber-50 p-3">
          {warnings.map((w, i) => (
            <p key={i} className="flex gap-2 text-sm text-amber-800">
              <span>⚠️</span>
              <span>{w}</span>
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
              <span className="shrink-0 text-sm font-semibold text-slate-700">
                {str(d.date)}
              </span>
            </div>
          )
        })}
      </div>
      {Object.values(summary).some(Boolean) && (
        <div className="grid grid-cols-2 gap-2 pt-1">
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
  const sorted = [...mods].sort(
    (a, b) => (PRIORITY_ORDER[str(a.priority)] ?? 9) - (PRIORITY_ORDER[str(b.priority)] ?? 9),
  )

  return (
    <div className="space-y-4 pt-1">
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
              </div>
              <p className="mb-1 text-sm text-slate-800">{str(mod.modification)}</p>
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
  const confidence = num(recommend.confidence)
  const rationale = str(recommend.rationale)
  const strengths = arr(recommend.key_strengths) as string[]
  const weaknesses = arr(recommend.key_weaknesses) as string[]
  const conditions = arr(recommend.conditions) as string[]
  const dimensions = arr(data.risk_dimensions) as Rec[]
  const actionItems = arr(data.action_items) as Rec[]
  const overallScore = num(data.overall_risk_score)
  const winProb = rec(data.estimated_win_probability)

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

// ── Main dispatcher ───────────────────────────────────────────────────────────
interface AnalysisDimViewProps {
  dimension: string
  data: Record<string, unknown>
}

export function AnalysisDimView({ dimension, data }: AnalysisDimViewProps) {
  switch (dimension) {
    case "qualification":
      return <QualificationView data={data} />
    case "evaluation":
      return <EvaluationView data={data} />
    case "key_dates":
      return <KeyDatesView data={data} />
    case "submission":
      return <SubmissionView data={data} />
    case "bds_modification":
      return <BDSView data={data} />
    case "methodology":
      return <MethodologyView data={data} />
    case "commercial":
      return <CommercialView data={data} />
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
