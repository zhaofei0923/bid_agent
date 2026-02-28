import axios from "axios"

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1",
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
})

// Request interceptor — attach JWT
apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token")
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

// Response interceptor — handle 401 refresh
apiClient.interceptors.response.use(
  (response) => {
    // Track credits from response headers
    const consumed = response.headers["x-credits-consumed"]
    const remaining = response.headers["x-credits-remaining"]
    if (consumed || remaining) {
      window.dispatchEvent(
        new CustomEvent("credits-update", {
          detail: {
            consumed: consumed ? Number(consumed) : 0,
            remaining: remaining ? Number(remaining) : undefined,
          },
        })
      )
    }
    return response
  },
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      try {
        const refreshToken = localStorage.getItem("refresh_token")
        if (!refreshToken) throw new Error("No refresh token")

        const { data } = await axios.post(
          `${apiClient.defaults.baseURL}/auth/refresh`,
          { refresh_token: refreshToken }
        )
        localStorage.setItem("access_token", data.access_token)
        localStorage.setItem("refresh_token", data.refresh_token)
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`
        return apiClient(originalRequest)
      } catch {
        localStorage.removeItem("access_token")
        localStorage.removeItem("refresh_token")
        if (typeof window !== "undefined") {
          const currentLocale = window.location.pathname.split("/")[1] || "zh"
          window.location.href = `/${currentLocale}/auth/login`
        }
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient
