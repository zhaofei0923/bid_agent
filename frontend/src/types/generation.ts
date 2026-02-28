export interface GuidanceMessage {
  role: "user" | "assistant"
  content: string
  timestamp: string
}

export interface GuidanceResponse {
  content: string
  credits_consumed: number
}

export interface GuidanceStreamEvent {
  type: "token" | "done" | "error"
  content?: string
  credits_consumed?: number
}

export interface ReviewDraftRequest {
  project_id: string
  section_key: string
  draft_content: string
}

export interface ReviewDraftResponse {
  score: number
  overall_feedback: string
  strengths: string[]
  improvements: string[]
  line_comments: Array<{
    line: number
    type: "suggestion" | "warning" | "error"
    content: string
  }>
  credits_consumed: number
}

export interface QualityReviewResult {
  overall_score: number
  dimensions: Array<{
    name: string
    score: number
    max_score: number
    findings: string[]
    suggestions: string[]
  }>
  risk_items: Array<{
    severity: "high" | "medium" | "low"
    description: string
    recommendation: string
  }>
  credits_consumed: number
}

export interface DocumentStructure {
  sections: Array<{
    key: string
    title: string
    page_start: number
    page_end: number
    summary?: string
  }>
}
