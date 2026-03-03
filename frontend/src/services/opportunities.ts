import axios from "axios"
import apiClient from "./api-client"
import type {
  Opportunity,
  OpportunitySearchParams,
  PaginatedResult,
} from "@/types"

/** Unauthenticated axios instance for public endpoints */
const publicClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1",
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
})

export const opportunityService = {
  async list(
    params: OpportunitySearchParams = {}
  ): Promise<PaginatedResult<Opportunity>> {
    const res = await apiClient.get<PaginatedResult<Opportunity>>(
      "/opportunities",
      { params }
    )
    return res.data
  },

  async getById(id: string): Promise<Opportunity> {
    const res = await apiClient.get<Opportunity>(`/opportunities/${id}`)
    return res.data
  },

  /** Public search — no JWT required, status forced to open on server */
  async publicSearch(
    params: Omit<OpportunitySearchParams, "status"> = {}
  ): Promise<PaginatedResult<Opportunity>> {
    const res = await publicClient.get<PaginatedResult<Opportunity>>(
      "/public/opportunities",
      { params }
    )
    return res.data
  },

  /** Latest opportunities — no JWT, for landing page / dashboard */
  async publicLatest(
    limit: number = 10,
    source?: string
  ): Promise<Opportunity[]> {
    const res = await publicClient.get<Opportunity[]>(
      "/public/opportunities/latest",
      { params: { limit, ...(source ? { source } : {}) } }
    )
    return res.data
  },
}
