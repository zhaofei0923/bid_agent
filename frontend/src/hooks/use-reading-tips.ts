import { useQuery } from "@tanstack/react-query"
import { readingTipsService } from "@/services/reading-tips"

export function useReadingTips(projectId: string, enabled = true) {
  return useQuery({
    queryKey: ["reading-tips", projectId],
    queryFn: () => readingTipsService.get(projectId),
    enabled: !!projectId && enabled,
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 1,
  })
}
