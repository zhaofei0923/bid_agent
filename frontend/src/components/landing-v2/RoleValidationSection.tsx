"use client"

import { memo } from "react"
import { useTranslations } from "next-intl"
import { BriefcaseBusiness, FilePenLine, WalletCards } from "lucide-react"
import { LandingV2RoleItem } from "./types"

const ROLE_ICONS = [BriefcaseBusiness, FilePenLine, WalletCards]

export const RoleValidationSection = memo(function RoleValidationSection() {
  const t = useTranslations("landingV2")
  const items = t.raw("roles.items") as LandingV2RoleItem[]

  return (
    <section className="mx-auto w-full max-w-[1320px] px-6 py-20">
      <div className="rounded-[36px] border border-stone-200 bg-[rgba(248,244,238,0.7)] px-6 py-10 sm:px-8 lg:px-10">
        <div className="max-w-3xl">
          <p className="landing-v2-kicker">{t("roles.label")}</p>
          <h2 className="landing-v2-display mt-4 max-w-2xl text-3xl font-semibold text-slate-950 sm:text-4xl">
            {t("roles.title")}
          </h2>
          <p className="mt-5 max-w-3xl text-base leading-8 text-stone-600">
            {t("roles.description")}
          </p>
        </div>

        <div className="mt-10 grid gap-4 lg:grid-cols-3">
          {items.map((item, index) => {
            const Icon = ROLE_ICONS[index]

            return (
              <div key={item.role} className="rounded-3xl border border-stone-200 bg-white px-5 py-6">
                <div className="flex h-11 w-11 items-center justify-center rounded-full bg-stone-100 text-slate-700">
                  <Icon className="h-5 w-5" />
                </div>
                <p className="mt-6 text-sm font-semibold tracking-[0.08em] text-stone-500">
                  {item.summary}
                </p>
                <h3 className="mt-3 text-xl font-semibold text-slate-900">
                  {item.role}
                </h3>
                <p className="mt-3 text-sm leading-7 text-stone-700">
                  {item.headline}
                </p>
                <div className="mt-5 space-y-3">
                  {item.bullets.map((bullet) => (
                    <div
                      key={bullet}
                      className="rounded-3xl bg-stone-50 px-4 py-3 text-sm leading-6 text-stone-600"
                    >
                      {bullet}
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
})
