"use client"

import { memo } from "react"
import { useTranslations } from "next-intl"
import { ArrowRightLeft, ClipboardCheck, Target } from "lucide-react"
import { LandingV2OutcomeItem } from "./types"

const OUTCOME_ICONS = [Target, ArrowRightLeft, ClipboardCheck]

export const ManagerOutcomesSection = memo(function ManagerOutcomesSection() {
  const t = useTranslations("landingV2")
  const items = t.raw("outcomes.items") as LandingV2OutcomeItem[]

  return (
    <section id="value" className="mx-auto w-full max-w-[1320px] px-6 py-20">
      <div className="max-w-3xl">
        <p className="landing-v2-kicker">{t("outcomes.label")}</p>
        <h2 className="landing-v2-display mt-4 text-3xl font-semibold text-slate-950 sm:text-4xl">
          {t("outcomes.title")}
        </h2>
        <p className="mt-5 text-base leading-8 text-stone-600">
          {t("outcomes.description")}
        </p>
      </div>

      <div className="mt-10 grid gap-5 lg:grid-cols-3">
        {items.map((item, index) => {
          const Icon = OUTCOME_ICONS[index]

          return (
            <div key={item.title} className="landing-v2-card flex h-full flex-col p-6">
              <div className="flex items-center justify-between">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-stone-100 text-slate-700">
                  <Icon className="h-5 w-5" />
                </div>
                <span className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">
                  0{index + 1}
                </span>
              </div>
              <h3 className="mt-8 text-xl font-semibold text-slate-950">{item.title}</h3>
              <p className="mt-3 text-sm leading-7 text-stone-600">{item.desc}</p>
              <div className="mt-6 space-y-3">
                {item.bullets.map((bullet) => (
                  <div
                    key={bullet}
                    className="flex items-start gap-3 rounded-3xl bg-stone-50 px-4 py-3 text-sm text-stone-700"
                  >
                    <span className="mt-1.5 h-2 w-2 rounded-full bg-slate-900" />
                    <span>{bullet}</span>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
})
