import apiClient from "./api-client"
import type { BidAnalysis } from "@/types/bid"

export const bidAnalysisService = {
  getByProject: async (projectId: string) => {
    const { data } = await apiClient.get<BidAnalysis>(
      `/projects/${projectId}/analysis`
    )
    return data
  },

  trigger: async (
    projectId: string,
    params?: { steps?: string[]; force_refresh?: boolean }
  ) => {
    const searchParams = new URLSearchParams()
    if (params?.force_refresh) {
      searchParams.append("force_refresh", "true")
    }
    if (params?.steps && params.steps.length > 0) {
      params.steps.forEach((step) => searchParams.append("steps", step))
    }

    const { data } = await apiClient.post(
      `/projects/${projectId}/analysis/trigger?${searchParams.toString()}`
    )
    return data
  },
}
