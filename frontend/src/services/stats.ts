import apiClient from "./api-client"

export interface OverviewStats {
  total_users: number
  total_projects: number
  total_opportunities: number
  total_analyses: number
  active_users_today: number
}

export interface DailyStat {
  date: string
  new_users: number
  new_projects: number
  api_calls: number
  credits_consumed: number
}

export interface UserStats {
  projects_count: number
  analyses_count: number
  credits_consumed: number
  last_active: string
}

export const statsService = {
  getOverview: async () => {
    const { data } = await apiClient.get<OverviewStats>("/stats/overview")
    return data
  },

  getDaily: async (startDate: string, endDate: string) => {
    const { data } = await apiClient.get<DailyStat[]>("/stats/daily", {
      params: { start_date: startDate, end_date: endDate },
    })
    return data
  },

  getMyStats: async () => {
    const { data } = await apiClient.get<UserStats>("/stats/users/me")
    return data
  },
}
