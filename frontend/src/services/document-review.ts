import apiClient from "./api-client"
import type { DocumentReviewResult } from "@/types/bid"

export interface ReviewItemParams {
  item_title: string
  item_guidance?: string
  source_section?: string
  source_excerpt?: string
  content_text?: string
  file?: File
}

export interface ReviewItemResponse {
  success: boolean
  data: DocumentReviewResult | null
  tokens_consumed: number
}

export const documentReviewService = {
  reviewItem: async (
    projectId: string,
    params: ReviewItemParams
  ): Promise<ReviewItemResponse> => {
    const formData = new FormData()
    formData.append("item_title", params.item_title)
    if (params.item_guidance) formData.append("item_guidance", params.item_guidance)
    if (params.source_section) formData.append("source_section", params.source_section)
    if (params.source_excerpt) formData.append("source_excerpt", params.source_excerpt)
    if (params.content_text) formData.append("content_text", params.content_text)
    if (params.file) formData.append("file", params.file)

    const { data } = await apiClient.post<ReviewItemResponse>(
      `/projects/${projectId}/document-review/item`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 120_000,
      }
    )
    return data
  },
}
