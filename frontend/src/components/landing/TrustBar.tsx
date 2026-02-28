"use client"

import { useTranslations } from "next-intl"

export function TrustBar() {
  const t = useTranslations("landing")
  const institutions = t.raw("institutions") as Array<{ name: string; abbr: string }>

  return (
    <section className="py-12 border-y bg-muted/30">
      <div className="container text-center">
        <p className="text-sm text-muted-foreground mb-8">{t("trustTitle")}</p>
        <div className="grid grid-cols-3 gap-8 max-w-lg mx-auto">
          {institutions.map((inst) => (
            <div
              key={inst.abbr}
              className="flex flex-col items-center gap-2 group"
            >
              <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center text-xl font-bold text-muted-foreground group-hover:text-foreground transition-colors">
                {inst.abbr}
              </div>
              <span className="text-xs text-muted-foreground">{inst.name}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
