"use client"

import { memo, useState, useRef, useEffect } from "react"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { useGuidanceStream } from "@/hooks/use-generation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useTranslations } from "next-intl"

type ChatMode = "bid_document" | "knowledge_base"

interface BidChatPanelProps {
  projectId: string
}

export const BidChatPanel = memo(function BidChatPanel({
  projectId,
}: BidChatPanelProps) {
  const { isChatPanelOpen, toggleChatPanel } = useBidWorkspaceStore()
  const t = useTranslations("workspace")
  const [mode, setMode] = useState<ChatMode>("bid_document")
  const { messages, isStreaming, streamingContent, send, stop, reset } =
    useGuidanceStream(projectId, mode)
  const [input, setInput] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, streamingContent])

  const handleModeChange = (newMode: ChatMode) => {
    if (newMode === mode) return
    reset()
    setMode(newMode)
  }

  if (!isChatPanelOpen) {
    return (
      <div className="app-section-frame flex w-12 shrink-0 flex-col items-center pt-4">
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
    <div className="app-section-frame flex w-[380px] shrink-0 flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-stone-200 px-4 py-3">
        <h3 className="text-sm font-semibold">{t("chat.title")}</h3>
        <button
          onClick={toggleChatPanel}
          className="text-sm text-stone-500 transition-colors duration-200 hover:text-slate-900"
        >
          ×
        </button>
      </div>

      {/* Mode Tabs */}
      <div className="flex border-b border-stone-200">
        <button
          className={`flex-1 py-2 text-xs font-medium transition-colors ${
            mode === "bid_document"
              ? "border-b-2 border-slate-900 text-slate-900"
              : "text-stone-500 hover:text-slate-700"
          }`}
          onClick={() => handleModeChange("bid_document")}
        >
          📄 {t("chat.modeDocuments")}
        </button>
        <button
          className={`flex-1 py-2 text-xs font-medium transition-colors ${
            mode === "knowledge_base"
              ? "border-b-2 border-slate-900 text-slate-900"
              : "text-stone-500 hover:text-slate-700"
          }`}
          onClick={() => handleModeChange("knowledge_base")}
        >
          📚 {t("chat.modeKnowledge")}
        </button>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 && !isStreaming && (
          <div className="app-surface-muted px-4 py-6 text-center text-sm text-muted-foreground">
            <p className="mb-2">{t("chat.greeting")}</p>
            <p className="mb-4 text-xs">
              {mode === "bid_document" ? t("chat.modeDocHint") : t("chat.modeKbHint")}
            </p>
            <div className="grid grid-cols-2 gap-2 px-2">
              {mode === "bid_document" ? (
                <>
                  <Button variant="outline" size="sm" className="text-xs h-auto py-2 justify-start text-left" onClick={() => send(t("chat.skills.extractDates"))}>
                    📅 {t("chat.skills.extractDates")}
                  </Button>
                  <Button variant="outline" size="sm" className="text-xs h-auto py-2 justify-start text-left" onClick={() => send(t("chat.skills.analyzeQualification"))}>
                    📋 {t("chat.skills.analyzeQualification")}
                  </Button>
                  <Button variant="outline" size="sm" className="text-xs h-auto py-2 justify-start text-left" onClick={() => send(t("chat.skills.evaluateCriteria"))}>
                    📊 {t("chat.skills.evaluateCriteria")}
                  </Button>
                  <Button variant="outline" size="sm" className="text-xs h-auto py-2 justify-start text-left" onClick={() => send(t("chat.skills.analyzeCommercial"))}>
                    💰 {t("chat.skills.analyzeCommercial")}
                  </Button>
                </>
              ) : (
                <>
                  <Button variant="outline" size="sm" className="text-xs h-auto py-2 justify-start text-left" onClick={() => send(t("chat.skills.writeTechnical"))}>
                    ✍️ {t("chat.skills.writeTechnical")}
                  </Button>
                  <Button variant="outline" size="sm" className="text-xs h-auto py-2 justify-start text-left" onClick={() => send(t("chat.skills.formatRequirements"))}>
                    📐 {t("chat.skills.formatRequirements")}
                  </Button>
                  <Button variant="outline" size="sm" className="text-xs h-auto py-2 justify-start text-left" onClick={() => send(t("chat.skills.winningStrategy"))}>
                    🏆 {t("chat.skills.winningStrategy")}
                  </Button>
                  <Button variant="outline" size="sm" className="text-xs h-auto py-2 justify-start text-left" onClick={() => send(t("chat.skills.commonMistakes"))}>
                    ⚠️ {t("chat.skills.commonMistakes")}
                  </Button>
                </>
              )}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-[22px] px-3 py-2 text-sm ${
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
            <div className="max-w-[85%] rounded-[22px] bg-stone-100 px-3 py-2 text-sm text-stone-700">
              <div className="whitespace-pre-wrap">{streamingContent}</div>
              <span className="animate-pulse">▌</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-stone-200 bg-white/40 p-4">
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
