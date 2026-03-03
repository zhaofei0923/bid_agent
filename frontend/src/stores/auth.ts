import { create } from "zustand"
import type { User, TokenResponse } from "@/types"
import { authService } from "@/services/auth"

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (
    email: string,
    password: string,
    name: string,
    company?: string
  ) => Promise<string>  // returns email to redirect to verify page
  setTokens: (tokens: TokenResponse) => Promise<void>
  logout: () => void
  loadUser: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  login: async (email, password) => {
    const tokens = await authService.login({ email, password })
    localStorage.setItem("access_token", tokens.access_token)
    localStorage.setItem("refresh_token", tokens.refresh_token)
    const user = await authService.getMe()
    set({ user, isAuthenticated: true })
  },

  register: async (email, password, name, company) => {
    const pending = await authService.register({ email, password, name, company })
    // Returns email for the caller to redirect to verify-email page
    return pending.email
  },

  setTokens: async (tokens) => {
    localStorage.setItem("access_token", tokens.access_token)
    localStorage.setItem("refresh_token", tokens.refresh_token)
    const user = await authService.getMe()
    set({ user, isAuthenticated: true })
  },

  logout: () => {
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    set({ user: null, isAuthenticated: false })
  },

  loadUser: async () => {
    try {
      const token = localStorage.getItem("access_token")
      if (!token) {
        set({ isLoading: false })
        return
      }
      const user = await authService.getMe()
      set({ user, isAuthenticated: true, isLoading: false })
    } catch {
      localStorage.removeItem("access_token")
      localStorage.removeItem("refresh_token")
      set({ user: null, isAuthenticated: false, isLoading: false })
    }
  },
}))
