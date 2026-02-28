import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { bidAnalysisService } from "@/services/bid-analysis"

export function useBidAnalysis(projectId: string) {
  return useQuery({
    queryKey: ["bid-analysis", projectId],
    queryFn: () => bidAnalysisService.getByProject(projectId),
    enabled: !!projectId,
    staleTime: 60_000,
  })
}

export function useTriggerAnalysis(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (params?: { steps?: string[]; force_refresh?: boolean }) =>
      bidAnalysisService.trigger(projectId, params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bid-analysis", projectId] })
    },
  })
}
