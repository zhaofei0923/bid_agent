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
  file_name: string
  file_type: string
  file_size: number
  document_type: "tor" | "rfp" | "other"
  upload_status: "uploading" | "uploaded" | "processing" | "completed" | "failed"
  created_at: string
}
