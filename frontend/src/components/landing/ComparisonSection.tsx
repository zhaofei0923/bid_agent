"use client"

import { useTranslations } from "next-intl"

export function ComparisonSection() {
  const t = useTranslations("landing")
  const rows = t.raw("comparisonRows") as Array<{ traditional: string; bidagent: string }>

  return (
    <section className="py-20 bg-muted/30">
      <div className="container">
        <h2 className="text-3xl font-bold text-center mb-12">
          {t("comparisonTitle")}
        </h2>
        <div className="max-w-3xl mx-auto rounded-xl overflow-hidden border">
          <div className="grid grid-cols-2">
            <div className="bg-red-50 px-6 py-3 text-center font-semibold text-red-700 border-b">
              {t("traditionalWay")}
            </div>
            <div className="bg-green-50 px-6 py-3 text-center font-semibold text-green-700 border-b">
              {t("bidagentWay")}
            </div>
          </div>
          {rows.map((row, i) => (
            <div key={i} className="grid grid-cols-2 border-b last:border-0">
              <div className="bg-red-50/50 px-6 py-3 text-sm text-red-800 flex items-center gap-2">
                <span className="text-red-400">✕</span> {row.traditional}
              </div>
              <div className="bg-green-50/50 px-6 py-3 text-sm text-green-800 flex items-center gap-2">
                <span className="text-green-500">✓</span> {row.bidagent}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
