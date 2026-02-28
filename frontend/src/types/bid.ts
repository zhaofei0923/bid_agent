export type BidStep =
  | "upload"
  | "overview"
  | "analysis"
  | "plan"
  | "writing"
  | "review"
  | "tracking"

export interface BidAnalysis {
  id: string
  project_id: string
  bid_type: string | null
  evaluation_criteria: Record<string, unknown> | null
  qualification_requirements: Record<string, unknown> | null
  scoring_breakdown: Record<string, unknown> | null
  risk_assessment: Record<string, unknown> | null
  key_dates: Record<string, unknown> | null
  created_at: string
}

export interface BidPlan {
  id: string
  project_id: string
  outline: Record<string, unknown> | null
  strategy: Record<string, unknown> | null
  tasks: BidPlanTask[]
  created_at: string
}

export interface BidPlanTask {
  id: string
  plan_id: string
  title: string
  description: string | null
  status: "pending" | "in_progress" | "completed"
  assigned_to: string | null
  due_date: string | null
  sort_order: number
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
