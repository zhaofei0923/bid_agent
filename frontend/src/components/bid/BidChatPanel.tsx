"use client"

import { memo, useState, useRef, useEffect } from "react"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { useGuidanceStream } from "@/hooks/use-generation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useTranslations } from "next-intl"

interface BidChatPanelProps {
  projectId: string
}

export const BidChatPanel = memo(function BidChatPanel({
  projectId,
}: BidChatPanelProps) {
  const { isChatPanelOpen, toggleChatPanel } = useBidWorkspaceStore()
  const t = useTranslations("workspace")
  const { messages, isStreaming, streamingContent, send, stop } =
    useGuidanceStream(projectId)
  const [input, setInput] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, streamingContent])

  if (!isChatPanelOpen) {
    return (
      <div className="ml-4 flex w-12 shrink-0 flex-col items-center rounded-[22px] border border-stone-200 bg-[rgba(255,255,255,0.92)] pt-4">
        <button
          onClick={toggleChatPanel}
          className="writing-mode-vertical text-sm font-medium text-stone-500 hover:text-slate-900"
          style={{ writingMode: "vertical-rl" }}
        >
          {t("chat.collapsed")}
        </button>
      </div>
    )
  }

  const handleSend = () => {
    const trimmed = input.trim()
    if (!trimmed || isStreaming) return
    send(trimmed)
    setInput("")
  }

  return (
    <div className="app-surface ml-4 flex w-[380px] shrink-0 flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-stone-200 px-4 py-3">
        <h3 className="text-sm font-semibold">{t("chat.title")}</h3>
        <button
          onClick={toggleChatPanel}
          className="text-sm text-stone-500 transition-colors duration-200 hover:text-slate-900"
        >
          ×
        </button>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 && !isStreaming && (
          <div className="text-center text-sm text-muted-foreground py-8">
            <p className="mb-2">{t("chat.greeting")}</p>
            <p className="mb-6">{t("chat.greetingHint")}</p>

            <div className="grid grid-cols-2 gap-2 px-2">
              <Button
                variant="outline"
                size="sm"
                className="text-xs h-auto py-2 justify-start text-left"
                onClick={() => send(t("chat.skills.extractDates") || "提取关键日期")}
              >
                📅 {t("chat.skills.extractDates") || "提取关键日期"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="text-xs h-auto py-2 justify-start text-left"
                onClick={() => send(t("chat.skills.analyzeQualification") || "分析资质要求")}
              >
                📋 {t("chat.skills.analyzeQualification") || "分析资质要求"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="text-xs h-auto py-2 justify-start text-left"
                onClick={() => send(t("chat.skills.evaluateCriteria") || "评估评分标准")}
              >
                📊 {t("chat.skills.evaluateCriteria") || "评估评分标准"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="text-xs h-auto py-2 justify-start text-left"
                onClick={() => send(t("chat.skills.analyzeCommercial") || "审查商务条款")}
              >
                💰 {t("chat.skills.analyzeCommercial") || "审查商务条款"}
              </Button>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                msg.role === "user"
                  ? "bg-slate-900 text-white"
                  : "bg-stone-100 text-stone-700"
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.content}</div>
            </div>
          </div>
        ))}

        {isStreaming && streamingContent && (
          <div className="flex justify-start">
            <div className="max-w-[85%] rounded-lg bg-stone-100 px-3 py-2 text-sm text-stone-700">
              <div className="whitespace-pre-wrap">{streamingContent}</div>
              <span className="animate-pulse">▌</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-stone-200 p-4">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            placeholder={t("chat.placeholder")}
            disabled={isStreaming}
            className="text-sm"
          />
          {isStreaming ? (
            <Button size="sm" variant="outline" onClick={stop}>
              {t("chat.stop")}
            </Button>
          ) : (
            <Button size="sm" onClick={handleSend} disabled={!input.trim()}>
              {t("chat.send")}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
})
