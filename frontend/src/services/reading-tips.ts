import apiClient from "./api-client"

export interface ReadingTipsSource {
  content: string
  source_document: string
  page_number: number | null
  score: number
}

export interface ReadingTipsResponse {
  reading_tips: string
  bidding_suggestions: string
  sources: ReadingTipsSource[]
}

export const readingTipsService = {
  get: async (projectId: string): Promise<ReadingTipsResponse> => {
    const { data } = await apiClient.post<ReadingTipsResponse>(
      `/projects/${projectId}/reading-tips`,
      null,
      { timeout: 120_000 }
    )
    return data
  },
}
