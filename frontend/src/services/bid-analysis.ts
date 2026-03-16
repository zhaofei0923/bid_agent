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

    // Analysis pipeline runs 12 LLM calls in 3 rounds — allow up to 10 minutes
    const { data } = await apiClient.post(
      `/projects/${projectId}/analysis/trigger?${searchParams.toString()}`,
      undefined,
      { timeout: 600_000 }
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
      `/projects/${projectId}/checklist/generate?force_refresh=${forceRefresh}`,
      undefined,
      // LLM generation can take 60-180s; align with Nginx proxy_read_timeout
      { timeout: 300_000 }
    )
    return data
  },
}
