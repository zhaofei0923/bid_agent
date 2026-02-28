"use client"

import { useState, useRef, useEffect } from "react"
import { useGuidanceStream } from "@/hooks/use-generation"
import { useTranslations } from "next-intl"

interface GenerationPanelProps {
  projectId: string
  sectionId?: string
  sectionTitle?: string
}

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
}

export default function GenerationPanel({
  projectId,
  sectionId,
  sectionTitle,
}: GenerationPanelProps) {
  const t = useTranslations("bid")
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const scrollRef = useRef<HTMLDivElement>(null)
  const { streamingContent, isStreaming, send } = useGuidanceStream(projectId)

  const prompts = (t.raw(`generation.sectionPrompts.${sectionId ?? "default"}`) ?? t.raw("generation.sectionPrompts.default")) as string[]

  useEffect(() => {
    scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight)
  }, [messages, streamingContent])

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return

    const question = input.trim()
    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: question,
    }
    setMessages((prev) => [...prev, userMsg])
    setInput("")

    try {
      send(question)

      if (streamingContent) {
        setMessages((prev) => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: streamingContent,
          },
        ])
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: t("generation.errorMessage"),
        },
      ])
    }
  }

  return (
    <div className="flex h-full flex-col rounded-xl border bg-white">
      {/* Header */}
      <div className="border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-lg">✏️</span>
          <div>
            <h3 className="font-semibold">{t("generation.title")}</h3>
            {sectionTitle && (
              <p className="text-xs text-gray-500">{t("generation.currentSection", { title: sectionTitle })}</p>
            )}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-3"
        style={{ minHeight: 300 }}
      >
        {messages.length === 0 && (
          <div className="py-8 text-center">
            <p className="text-sm text-gray-500">
              {t("generation.guideHint")}
            </p>
            <div className="mt-4 space-y-2">
              {prompts.map((q) => (
                <button
                  key={q}
                  onClick={() => setInput(q)}
                  className="block w-full rounded-lg border p-3 text-left text-sm hover:bg-gray-50"
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
              className={`max-w-[85%] rounded-lg px-4 py-2.5 text-sm whitespace-pre-wrap ${
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
            <div className="max-w-[85%] rounded-lg bg-gray-100 px-4 py-2.5 text-sm text-gray-800 whitespace-pre-wrap">
              {streamingContent}
              <span className="ml-1 animate-pulse">▌</span>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t p-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            placeholder={t("generation.inputPlaceholder")}
            disabled={isStreaming}
            className="flex-1 rounded-lg border px-3 py-2 text-sm disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isStreaming}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {isStreaming ? t("generation.generating") : t("generation.send")}
          </button>
        </div>
      </div>
    </div>
  )
}
