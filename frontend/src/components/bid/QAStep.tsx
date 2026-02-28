"use client"

import { memo, useState } from "react"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { useGuidanceStream } from "@/hooks/use-generation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { useTranslations } from "next-intl"

interface QAStepProps {
  projectId: string
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
          <CardContent className="p-4 space-y-4 max-h-[500px] overflow-y-auto">
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
