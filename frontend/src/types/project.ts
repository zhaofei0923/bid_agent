export type ProjectStatus =
  | "created"
  | "analyzing"
  | "analyzed"
  | "guiding"
  | "completed"
  | "archived"

export interface Project {
  id: string
  name: string
  description: string | null
  status: ProjectStatus
  opportunity_id: string | null
  user_id: string
  progress: number
  current_step: string | null
  institution: string | null
  is_saved: boolean
  combined_ai_overview: string | null
  combined_ai_reading_tips: string | null
  created_at: string
  updated_at: string
}

export interface ProjectCreate {
  name: string
  description?: string
  opportunity_id?: string
}

export interface ProjectUpdate {
  name?: string
  description?: string
  status?: ProjectStatus
  is_saved?: boolean
}

export interface ProjectDocument {
  id: string
  project_id: string
  filename: string
  original_filename: string
  file_size: number | null
  file_hash: string | null
  status: string
  processing_progress: number
  page_count: number | null
  processed_pages: number
  chunk_count: number
  vectorized_chunk_count: number
  error_message: string | null
  is_scanned: boolean
  ocr_confidence: number | null
  original_language: string
  ai_overview: string | null
  ai_reading_tips: string | null
  detected_institution: string | null
  analysis_generated_at: string | null
  created_at: string
  updated_at: string
}

export interface DocumentSection {
  id: string
  bid_document_id: string
  section_type: string
  section_title: string | null
  section_number: string | null
  start_page: number
  end_page: number
  content_preview: string | null
  detected_by: string
  confidence: number | null
  ai_summary: string | null
  reading_guide: string | null
  created_at: string
}
