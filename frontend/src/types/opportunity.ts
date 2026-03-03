export interface Opportunity {
  id: string
  source: "adb" | "wb"
  external_id: string
  url: string | null
  title: string
  project_number: string | null
  description: string | null
  organization: string | null
  published_at: string | null
  deadline: string | null
  budget_min: number | null
  budget_max: number | null
  currency: string | null
  location: string | null
  country: string | null
  sector: string | null
  procurement_type: string | null
  status: "open" | "closed" | "cancelled"
  created_at: string
  updated_at: string
}

export interface OpportunitySearchParams {
  page?: number
  page_size?: number
  source?: string
  status?: string
  country?: string
  sector?: string
  search?: string
  sort_by?: string
  sort_order?: "asc" | "desc"
}

export interface PaginatedResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}
