"use client"

import { memo, useState } from "react"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { useGuidanceStream } from "@/hooks/use-generation"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { useTranslations } from "next-intl"
import type { Source } from "@/types/generation"

interface QAStepProps {
  projectId: string
}

function SourceCitations({ sources }: { sources: Source[] }) {
  if (!sources.length) return null
  return (
    <div className="mt-2 space-y-1">
      <p className="text-xs text-muted-foreground font-medium">引用来源：</p>
      {sources.map((src, i) => (
        <div
          key={i}
          className="text-xs bg-blue-50 border border-blue-100 rounded px-2 py-1 flex items-start gap-2"
        >
          <Badge variant="outline" className="text-[10px] px-1 py-0 shrink-0">
            来源 {i + 1}
          </Badge>
          <div className="min-w-0">
            <span className="font-medium text-blue-700">
              {src.filename}
              {src.page_number ? ` · 第${src.page_number}页` : ""}
              {src.section_title ? ` · ${src.section_title}` : ""}
            </span>
            <p className="text-gray-600 line-clamp-2 mt-0.5">{src.content}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

export const QAStep = memo(function QAStep({ projectId }: QAStepProps) {
  const { completeStep, goToStep } = useBidWorkspaceStore()
  const t = useTranslations("bid")
  const suggestedQuestions = t.raw("qa.suggestedQuestions") as string[]
  const { messages, isStreaming, streamingContent, send, stop } =
    useGuidanceStream(projectId)
  const [input, setInput] = useState("")

  const handleSend = (question?: string) => {
    const q = question || input.trim()
    if (!q || isStreaming) return
    send(q)
    setInput("")
  }

  const handleNext = () => {
    completeStep("writing")
    goToStep("review")
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">{t("qa.title")}</h2>
        <p className="text-muted-foreground text-sm mt-1">
          {t("qa.subtitle")}
        </p>
      </div>

      {/* Suggested questions */}
      {messages.length === 0 && (
        <div className="grid grid-cols-2 gap-2">
          {suggestedQuestions.map((q) => (
            <button
              key={q}
              onClick={() => handleSend(q)}
              className="text-left text-sm p-3 rounded-lg border hover:bg-muted transition-colors"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Conversation */}
      {(messages.length > 0 || isStreaming) && (
        <Card>
          <CardContent className="p-4 space-y-4 max-h-[600px] overflow-y-auto">
            {messages.map((msg, i) => (
              <div key={i}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-semibold">
                    {msg.role === "user" ? t("qa.userLabel") : t("qa.aiLabel")}
                  </span>
                </div>
                <div
                  className={`text-sm whitespace-pre-wrap rounded-lg p-3 ${
                    msg.role === "user" ? "bg-primary/5" : "bg-muted"
                  }`}
                >
                  {msg.content}
                </div>
                {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
                  <SourceCitations sources={msg.sources} />
                )}
              </div>
            ))}
            {isStreaming && streamingContent && (
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-semibold">{t("qa.aiLabel")}</span>
                </div>
                <div className="text-sm whitespace-pre-wrap rounded-lg p-3 bg-muted">
                  {streamingContent}
                  <span className="animate-pulse">▌</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Input */}
      <div className="flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
          placeholder={t("qa.inputPlaceholder")}
          disabled={isStreaming}
        />
        {isStreaming ? (
          <Button variant="outline" onClick={stop}>
            {t("qa.stop")}
          </Button>
        ) : (
          <Button onClick={() => handleSend()} disabled={!input.trim()}>
            {t("qa.send")}
          </Button>
        )}
      </div>

      <div className="flex justify-end">
        <Button onClick={handleNext}>{t("qa.nextStep")}</Button>
      </div>
    </div>
  )
})
