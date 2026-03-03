import { useQuery } from "@tanstack/react-query"
import { opportunityService } from "@/services/opportunities"
import type { OpportunitySearchParams } from "@/types"

export function useOpportunities(params: OpportunitySearchParams = {}) {
  return useQuery({
    queryKey: ["opportunities", params],
    queryFn: () => opportunityService.list(params),
  })
}

export function useOpportunity(id: string) {
  return useQuery({
    queryKey: ["opportunity", id],
    queryFn: () => opportunityService.getById(id),
    enabled: !!id,
  })
}

/** Public search hook — no auth required */
export function usePublicOpportunities(
  params: Omit<OpportunitySearchParams, "status"> = {}
) {
  return useQuery({
    queryKey: ["public-opportunities", params],
    queryFn: () => opportunityService.publicSearch(params),
  })
}

/** Latest opportunities hook — for landing page & dashboard */
export function useLatestOpportunities(limit: number = 10, source?: string) {
  return useQuery({
    queryKey: ["latest-opportunities", limit, source],
    queryFn: () => opportunityService.publicLatest(limit, source),
    staleTime: 5 * 60 * 1000, // 5 min
  })
}
