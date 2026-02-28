"use client"

import { memo } from "react"
import { useTranslations } from "next-intl"
import { FileCheck2, FileSearch, Search, Users2 } from "lucide-react"
import { LandingV2CapabilityItem } from "./types"

const CAPABILITY_ICONS = [Search, FileSearch, Users2, FileCheck2]

export const CapabilitiesSection = memo(function CapabilitiesSection() {
  const t = useTranslations("landingV2")
  const items = t.raw("capabilities.items") as LandingV2CapabilityItem[]

  return (
    <section id="capabilities" className="mx-auto w-full max-w-[1320px] px-6 py-20">
      <div className="grid gap-10 lg:grid-cols-[0.88fr_1.12fr]">
        <div>
          <p className="landing-v2-kicker">{t("capabilities.label")}</p>
          <h2 className="landing-v2-display mt-4 max-w-lg text-3xl font-semibold text-slate-950 sm:text-4xl">
            {t("capabilities.title")}
          </h2>
          <p className="mt-5 max-w-xl text-base leading-8 text-stone-600">
            {t("capabilities.intro")}
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {items.map((item, index) => {
            const Icon = CAPABILITY_ICONS[index]

            return (
              <div key={item.title} className="landing-v2-card flex h-full flex-col p-6">
                <div className="flex items-center justify-between">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-stone-100 text-slate-700">
                    <Icon className="h-5 w-5" />
                  </div>
                  <span className="rounded-full bg-stone-100 px-3 py-1 text-xs font-semibold tracking-[0.08em] text-stone-600">
                    {item.statLabel}
                  </span>
                </div>
                <h3 className="mt-8 text-xl font-semibold text-slate-950">{item.title}</h3>
                <p className="mt-3 max-w-xl text-sm leading-7 text-stone-600">
                  {item.desc}
                </p>
                <p className="mt-6 text-sm font-semibold text-slate-900">{item.stat}</p>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
})
