"use client"

import { memo } from "react"
import { useTranslations } from "next-intl"
import { LandingV2Institution } from "./types"

export const CoverageTrustSection = memo(function CoverageTrustSection() {
  const t = useTranslations("landingV2")
  const institutions = t.raw("trust.institutions") as LandingV2Institution[]

  return (
    <section className="px-6 py-10">
      <div className="mx-auto w-full max-w-[1320px] rounded-[36px] border border-stone-200 bg-[rgba(249,245,238,0.7)] px-6 py-10 sm:px-8 lg:px-10">
        <div className="grid gap-8 lg:grid-cols-[0.82fr_1.18fr] lg:items-center">
          <div>
            <p className="landing-v2-kicker">{t("trust.label")}</p>
            <h2 className="landing-v2-display mt-4 max-w-xl text-3xl font-semibold text-slate-950 sm:text-4xl">
              {t("trust.title")}
            </h2>
            <p className="mt-5 max-w-xl text-base leading-8 text-stone-600">
              {t("trust.description")}
            </p>
          </div>

          <div className="grid gap-3 md:grid-cols-3">
            {institutions.map((institution) => (
              <div key={institution.name} className="rounded-3xl border border-stone-200 bg-white px-5 py-6">
                <h3 className="text-lg font-semibold text-slate-900">
                  {institution.name}
                </h3>
                <p className="mt-3 text-sm leading-7 text-stone-600">
                  {institution.detail}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
})
