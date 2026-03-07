import apiClient from "./api-client"
import type { BidAnalysis } from "@/types/bid"

export const bidAnalysisService = {
  getByProject: async (projectId: string): Promise<BidAnalysis | null> => {
    try {
      const { data } = await apiClient.get<BidAnalysis>(
        `/projects/${projectId}/analysis`
      )
      return data
    } catch (err: unknown) {
      // 404 means no analysis yet — return null so the component shows the start button
      const status = (err as { response?: { status?: number } })?.response?.status
      if (status === 404) return null
      throw err
    }
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

    // Analysis pipeline runs 8 LLM calls synchronously — allow up to 5 minutes
    const { data } = await apiClient.post(
      `/projects/${projectId}/analysis/trigger?${searchParams.toString()}`,
      undefined,
      { timeout: 300_000 }
    )
    return data
  },
}

export const checklistService = {
  generate: async (
    projectId: string,
    forceRefresh = false
  ): Promise<import("@/types/bid").SubmissionChecklist> => {
    const { data } = await apiClient.post(
      `/projects/${projectId}/checklist/generate?force_refresh=${forceRefresh}`
    )
    return data
  },
}
