import apiClient from "./api-client"

export interface KnowledgeBase {
  id: string
  name: string
  institution: "adb" | "wb" | "afdb"
  kb_type: "guide" | "review" | "template"
  description: string | null
  document_count: number
  chunk_count: number
  created_at: string
  updated_at: string
}

export interface KnowledgeSearchResult {
  chunk_id: string
  content: string
  score: number
  source_document: string
  metadata: Record<string, unknown>
}

export const knowledgeBaseService = {
  list: async () => {
    const { data } = await apiClient.get<KnowledgeBase[]>("/knowledge-bases")
    return data
  },

  getById: async (id: string) => {
    const { data } = await apiClient.get<KnowledgeBase>(`/knowledge-bases/${id}`)
    return data
  },

  create: async (params: {
    name: string
    description?: string
    institution: "adb" | "wb" | "afdb"
    kb_type: "guide" | "review" | "template"
  }) => {
    const { data } = await apiClient.post<KnowledgeBase>("/knowledge-bases", params)
    return data
  },

  search: async (query: string, institution?: string, topK?: number) => {
    const { data } = await apiClient.post<KnowledgeSearchResult[]>(
      "/knowledge-bases/search",
      { query, institution, top_k: topK }
    )
    return data
  },
}
