import apiClient from "./api-client"
import type { LoginRequest, RegisterRequest, TokenResponse, User } from "@/types"

export const authService = {
  async login(data: LoginRequest): Promise<TokenResponse> {
    const res = await apiClient.post<TokenResponse>("/auth/login", data)
    return res.data
  },

  async register(data: RegisterRequest): Promise<TokenResponse> {
    const res = await apiClient.post<TokenResponse>("/auth/register", data)
    return res.data
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
