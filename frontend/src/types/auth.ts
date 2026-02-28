export interface User {
  id: string
  email: string
  name: string
  company: string | null
  avatar_url: string | null
  role: "user" | "admin"
  language: "zh" | "en"
  credits_balance: number
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  name: string
  company?: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}
