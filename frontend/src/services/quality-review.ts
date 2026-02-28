import apiClient from "./api-client"
import type { QualityReviewResult } from "@/types/generation"

export const qualityReviewService = {
  fullReview: async (projectId: string, proposalContent: string) => {
    const { data } = await apiClient.post<QualityReviewResult>(
      `/projects/${projectId}/quality-review/full`,
      { proposal_content: proposalContent }
    )
    return data
  },

  quickReview: async (projectId: string, proposalContent: string) => {
    const { data } = await apiClient.post<QualityReviewResult>(
      `/projects/${projectId}/quality-review/quick`,
      { proposal_content: proposalContent }
    )
    return data
  },
}
