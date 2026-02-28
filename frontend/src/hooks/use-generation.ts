import { useState, useCallback, useRef } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { generationService } from "@/services/generation"
import type { GuidanceMessage, GuidanceStreamEvent } from "@/types/generation"

export function useGuidance(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (message: string) => generationService.ask(projectId, message),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["guidance-conversation", projectId],
      })
    },
  })
}

export function useGuidanceStream(projectId: string) {
  const [messages, setMessages] = useState<GuidanceMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState("")
  const abortRef = useRef<(() => void) | null>(null)

  const send = useCallback(
    (message: string) => {
      setMessages((prev) => [
        ...prev,
        { role: "user", content: message, timestamp: new Date().toISOString() },
      ])
      setIsStreaming(true)
      setStreamingContent("")

      let accumulated = ""

      const cancel = generationService.askStream(
        projectId,
        message,
        (event: GuidanceStreamEvent) => {
          if (event.type === "token" && event.content) {
            accumulated += event.content
            setStreamingContent(accumulated)
          } else if (event.type === "done") {
            setMessages((prev) => [
              ...prev,
              {
                role: "assistant",
                content: accumulated,
                timestamp: new Date().toISOString(),
              },
            ])
            setStreamingContent("")
            setIsStreaming(false)
          } else if (event.type === "error") {
            setIsStreaming(false)
            setStreamingContent("")
          }
        }
      )

      abortRef.current = cancel
    },
    [projectId]
  )

  const stop = useCallback(() => {
    abortRef.current?.()
    setIsStreaming(false)
  }, [])

  const reset = useCallback(() => {
    setMessages([])
    setStreamingContent("")
    setIsStreaming(false)
  }, [])

  return { messages, isStreaming, streamingContent, send, stop, reset }
}
