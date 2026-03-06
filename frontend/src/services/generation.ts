import apiClient from "./api-client"
import type { GuidanceResponse, GuidanceStreamEvent } from "@/types/generation"

export const generationService = {
  ask: async (projectId: string, message: string) => {
    const { data } = await apiClient.post<GuidanceResponse>(
      `/projects/${projectId}/guidance`,
      { message }
    )
    return data
  },

  askStream: (
    projectId: string,
    message: string,
    onEvent: (event: GuidanceStreamEvent) => void,
    contextType?: string
  ) => {
    const controller = new AbortController()

    const run = async () => {
      const authToken = localStorage.getItem("access_token") || ""

      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1"
      const response = await fetch(
        `${baseUrl}/projects/${projectId}/guidance/stream`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${authToken}`,
          },
          body: JSON.stringify({ message, context_type: contextType }),
          signal: controller.signal,
        }
      )

      if (!response.ok) {
        onEvent({ type: "error", content: `HTTP ${response.status}` })
        return
      }

      const reader = response.body?.getReader()
      if (!reader) return

      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() || ""

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const payload = line.slice(6).trim()
            if (payload === "[DONE]") {
              onEvent({ type: "done" })
              return
            }
            try {
              const parsed = JSON.parse(payload)
              // Route by event type from backend
              if (parsed.type === "content" && parsed.content) {
                onEvent({ type: "token", content: parsed.content })
              } else if (parsed.type === "sources" && parsed.sources) {
                onEvent({ type: "sources", sources: parsed.sources })
              } else if (parsed.type === "done") {
                onEvent({ type: "done" })
                return
              } else if (parsed.type === "error") {
                onEvent({ type: "error", content: parsed.message || "Stream error" })
              } else if (parsed.content) {
                // Fallback: treat any content field as token
                onEvent({ type: "token", content: parsed.content })
              }
            } catch {
              onEvent({ type: "token", content: payload })
            }
          }
        }
      }
      onEvent({ type: "done" })
    }

    run().catch((err) => {
      if (err.name !== "AbortError") {
        onEvent({ type: "error", content: err.message })
      }
    })

    return () => controller.abort()
  },
}
