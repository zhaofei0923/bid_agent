"use client"

import { useState, useRef, useEffect } from "react"
import { useTranslations } from "next-intl"
import { useGuidanceStream } from "@/hooks/use-generation"

interface BidAssistantProps {
  projectId?: string
  className?: string
}

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
}

export default function BidAssistant({ projectId, className = "" }: BidAssistantProps) {
  const t = useTranslations("knowledgeBase")
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const scrollRef = useRef<HTMLDivElement>(null)
  const { streamingContent, isStreaming, send } = useGuidanceStream(projectId ?? "")

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, streamingContent])

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
    }
    setMessages((prev) => [...prev, userMsg])
    setInput("")

    try {
      send(userMsg.content)

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: streamingContent || "...",
        },
      ])
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: t("errorMessage"),
        },
      ])
    }
  }

  const QUICK_QUESTIONS = t.raw("quickQuestions") as string[]

  return (
    <div className={`flex flex-col rounded-xl border bg-white ${className}`}>
      <div className="border-b px-4 py-3">
        <h3 className="font-semibold">{t("title")}</h3>
        <p className="text-xs text-gray-500">{t("subtitle")}</p>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3" style={{ maxHeight: 400 }}>
        {messages.length === 0 && (
          <div className="text-center text-sm text-gray-400 py-8">
            <p>{t("greeting")}</p>
            <p className="mt-1">{t("greetingHint")}</p>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              {QUICK_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => setInput(q)}
                  className="rounded-full border px-3 py-1 text-xs hover:bg-gray-50"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-800"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {isStreaming && streamingContent && (
          <div className="flex justify-start">
            <div className="max-w-[80%] rounded-lg bg-gray-100 px-4 py-2 text-sm text-gray-800">
              {streamingContent}
              <span className="ml-1 animate-pulse">▌</span>
            </div>
          </div>
        )}
      </div>

      <div className="border-t p-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            placeholder={t("inputPlaceholder")}
            disabled={isStreaming}
            className="flex-1 rounded-lg border px-3 py-2 text-sm disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isStreaming}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white disabled:opacity-50"
          >
            {t("send")}
          </button>
        </div>
      </div>
    </div>
  )
}
