import apiClient from "./api-client"

export interface AdminUser {
  id: string
  email: string
  name: string
  company: string | null
  role: "user" | "admin"
  credits_balance: number
  is_verified: boolean
  created_at: string
}

export interface AdminUserListResponse {
  items: AdminUser[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface AdminTransaction {
  id: string
  type: string
  amount: number
  balance_before: number
  balance_after: number
  description: string | null
  created_at: string
}

export interface AdminCreditAdjustResponse {
  new_balance: number
  transaction_id: string
}

export const adminService = {
  listUsers: async (params?: { search?: string; page?: number; page_size?: number }) => {
    const { data } = await apiClient.get<AdminUserListResponse>("/admin/users", {
      params,
    })
    return data
  },

  getUser: async (userId: string) => {
    const { data } = await apiClient.get<AdminUser>(`/admin/users/${userId}`)
    return data
  },

  adjustCredits: async (userId: string, amount: number, reason: string) => {
    const { data } = await apiClient.post<AdminCreditAdjustResponse>(
      `/admin/users/${userId}/credits/adjust`,
      { amount, reason }
    )
    return data
  },

  getUserTransactions: async (userId: string, page = 1, pageSize = 20) => {
    const { data } = await apiClient.get<AdminTransaction[]>(
      `/admin/users/${userId}/transactions`,
      { params: { page, page_size: pageSize } }
    )
    return data
  },

  updateUserRole: async (userId: string, role: "user" | "admin") => {
    const { data } = await apiClient.put<AdminUser>(`/admin/users/${userId}/role`, { role })
    return data
  },
}
