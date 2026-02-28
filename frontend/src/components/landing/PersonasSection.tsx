"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"

export function PersonasSection() {
  const t = useTranslations("landing")
  const personas = t.raw("personas") as Array<{
    role: string
    name: string
    quote: string
    features: string[]
  }>
  const [active, setActive] = useState(0)

  return (
    <section className="py-20">
      <div className="container">
        <h2 className="text-3xl font-bold text-center mb-12">
          {t("personasTitle")}
        </h2>

        <div className="flex justify-center gap-4 mb-8">
          {personas.map((p, i) => (
            <button
              key={i}
              onClick={() => setActive(i)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                i === active
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              {p.role}
            </button>
          ))}
        </div>

        <div className="max-w-2xl mx-auto rounded-xl border bg-background p-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-lg">
              👤
            </div>
            <div>
              <p className="font-semibold">{personas[active].role}</p>
              <p className="text-sm text-muted-foreground">
                {personas[active].name}
              </p>
            </div>
          </div>

          <blockquote className="border-l-4 border-primary/30 pl-4 mb-6 italic text-muted-foreground">
            &ldquo;{personas[active].quote}&rdquo;
          </blockquote>

          <div>
            <p className="text-sm font-medium mb-2">{t("coreFeatures")}</p>
            <ul className="space-y-1">
              {personas[active].features.map((f) => (
                <li key={f} className="text-sm text-muted-foreground flex items-center gap-2">
                  <span className="text-primary">·</span> {f}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  )
}
