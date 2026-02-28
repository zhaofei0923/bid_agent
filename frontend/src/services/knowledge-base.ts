import apiClient from "./api-client"

export interface KnowledgeBase {
  id: string
  name: string
  description: string | null
  institution: string | null
  user_id: string
  created_at: string
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
    institution?: string
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
