export type BidStep =
  | "upload"
  | "overview"
  | "plan"
  | "writing"
  | "review"

export interface BidAnalysis {
  id: string
  project_id: string
  bid_type: string | null
  executive_summary: Record<string, unknown> | null
  qualification_requirements: Record<string, unknown> | null
  evaluation_criteria: Record<string, unknown> | null
  evaluation_methodology: Record<string, unknown> | null
  commercial_terms: Record<string, unknown> | null
  submission_checklist: Record<string, unknown> | null
  key_dates: Record<string, unknown> | null
  bds_modifications: Record<string, unknown> | null
  technical_requirements: Record<string, unknown> | null
  technical_strategy: Record<string, unknown> | null
  compliance_matrix: Record<string, unknown> | null
  risk_assessment: Record<string, unknown> | null
  budget_info: Record<string, unknown> | null
  scoring_breakdown: Record<string, unknown> | null
  quality_review: Record<string, unknown> | null
  special_notes: string | null
  tokens_consumed: number
  created_at: string
  updated_at: string
}

export interface BidPlan {
  id: string
  project_id: string
  name: string | null
  description: string | null
  outline: Record<string, unknown> | null
  strategy: Record<string, unknown> | null
  generated_by_ai: boolean
  total_tasks: number | null
  completed_tasks: number | null
  tasks: BidPlanTask[]
  created_at: string
  updated_at: string
}

export type TaskCategory =
  | "documents"
  | "team"
  | "technical"
  | "experience"
  | "financial"
  | "compliance"
  | "submission"
  | "review"

export interface BidPlanTask {
  id: string
  plan_id: string
  title: string
  description: string | null
  status: "pending" | "in_progress" | "completed"
  category: TaskCategory | null
  priority: "high" | "medium" | "low" | null
  assigned_to: string | null
  start_date: string | null
  due_date: string | null
  sort_order: number
  notes: string | null
  related_document: string | null
  reference_page: number | null
}

// ── 旧分类 → 新分类映射 ─────────────────────────────────────────
const LEGACY_CATEGORY_MAP: Record<string, TaskCategory> = {
  commercial: "financial",
  administrative: "documents",
}

const VALID_CATEGORIES = new Set<string>([
  "documents", "team", "technical", "experience",
  "financial", "compliance", "submission", "review",
])

/** Normalize legacy 4-category values to the new 8-category system. */
export function normalizeCategory(raw: string | null | undefined): TaskCategory | null {
  if (!raw) return null
  if (VALID_CATEGORIES.has(raw)) return raw as TaskCategory
  return (LEGACY_CATEGORY_MAP[raw] as TaskCategory) ?? null
}

export interface GuidanceRequest {
  project_id: string
  section_key: string
  user_message: string
  context?: Record<string, unknown>
}

export interface GuidanceResponse {
  message: string
  suggestions: string[]
  references: string[]
  credits_consumed: number
}

// ── Submission Checklist ──────────────────────────────────────────

export interface ChecklistSource {
  filename: string
  page_number: number | null
  section_title: string
  excerpt: string
}

export interface ChecklistItem {
  id: string
  title: string
  required: boolean
  copies: number | null
  format_hint: string | null
  form_reference: string | null
  guidance: string
  source: ChecklistSource
}

export interface ChecklistSection {
  id: string
  title: string
  icon: string
  items: ChecklistItem[]
}

export interface SubmissionChecklist {
  project_id: string
  institution: string
  sections: ChecklistSection[]
  generated_at: string
  cached: boolean
}

export interface DocumentReviewResult {
  score: number
  meets_requirements: boolean
  gaps: string[]
  suggestions: string[]
  knowledge_tips: string[]
}
