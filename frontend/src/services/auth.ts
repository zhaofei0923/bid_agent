import apiClient from "./api-client"
import type { LoginRequest, RegisterRequest, TokenResponse, User } from "@/types"

export interface RegisterPendingResponse {
  need_verify: boolean
  email: string
  message: string
}

export const authService = {
  async login(data: LoginRequest): Promise<TokenResponse> {
    const res = await apiClient.post<TokenResponse>("/auth/login", data)
    return res.data
  },

  async register(data: RegisterRequest): Promise<RegisterPendingResponse> {
    const res = await apiClient.post<RegisterPendingResponse>("/auth/register", data)
    return res.data
  },

  async verifyEmail(email: string, code: string): Promise<TokenResponse> {
    const res = await apiClient.post<TokenResponse>("/auth/verify-email", { email, code })
    return res.data
  },

  async resendVerification(email: string): Promise<void> {
    await apiClient.post("/auth/resend-verification", { email })
  },

  async refresh(refreshToken: string): Promise<TokenResponse> {
    const res = await apiClient.post<TokenResponse>("/auth/refresh", {
      refresh_token: refreshToken,
    })
    return res.data
  },

  async getMe(): Promise<User> {
    const res = await apiClient.get<User>("/auth/me")
    return res.data
  },

  async updateMe(data: Partial<User>): Promise<User> {
    const res = await apiClient.put<User>("/auth/me", data)
    return res.data
  },

  async changePassword(current: string, newPwd: string): Promise<void> {
    await apiClient.put("/auth/password", {
      current_password: current,
      new_password: newPwd,
    })
  },
}
