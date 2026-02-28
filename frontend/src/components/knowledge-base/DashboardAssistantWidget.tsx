"use client"

import { useState } from "react"
import Link from "next/link"
import { useLocale, useTranslations } from "next-intl"

export default function DashboardAssistantWidget() {
  const locale = useLocale()
  const t = useTranslations("knowledgeBase")
  const [query, setQuery] = useState("")

  const TIPS = t.raw("widget.tips") as string[]

  return (
    <div className="rounded-xl border bg-gradient-to-br from-blue-50 to-indigo-50 p-6">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600 text-white">
          🤖
        </div>
        <div>
          <h3 className="font-semibold">{t("widget.title")}</h3>
          <p className="text-xs text-gray-500">{t("widget.subtitle")}</p>
        </div>
      </div>

      <div className="mt-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t("widget.inputPlaceholder")}
            className="flex-1 rounded-lg border bg-white px-3 py-2 text-sm"
          />
          <Link
            href={`/${locale}/help`}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 transition"
          >
            {t("widget.ask")}
          </Link>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {TIPS.map((tip) => (
          <button
            key={tip}
            onClick={() => setQuery(tip)}
            className="rounded-full border border-blue-200 bg-white px-3 py-1 text-xs text-blue-700 hover:bg-blue-50"
          >
            {tip}
          </button>
        ))}
      </div>
    </div>
  )
}
