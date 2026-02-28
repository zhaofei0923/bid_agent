"use client"

import Link from "next/link"
import { memo } from "react"
import { useTranslations } from "next-intl"
import { ArrowRight, Check } from "lucide-react"
import { LandingV2PlanItem } from "./types"

interface PricingV2SectionProps {
  locale: string
}

export const PricingV2Section = memo(function PricingV2Section({
  locale,
}: PricingV2SectionProps) {
  const t = useTranslations("landingV2")
  const plans = t.raw("pricing.plans") as LandingV2PlanItem[]
  const corePlans = plans.slice(0, 2)
  const enterprisePlan = plans[2]

  return (
    <section id="pricing" className="mx-auto w-full max-w-[1320px] px-6 py-20">
      <div className="max-w-3xl">
        <p className="landing-v2-kicker">{t("pricing.label")}</p>
        <h2 className="landing-v2-display mt-4 text-3xl font-semibold text-slate-950 sm:text-4xl">
          {t("pricing.title")}
        </h2>
        <p className="mt-5 text-base leading-8 text-stone-600">
          {t("pricing.description")}
        </p>
      </div>

      <div className="mt-10 grid gap-5 lg:grid-cols-2">
        {corePlans.map((plan, index) => {
          const primaryPlan = index === 1

          return (
            <div
              key={plan.name}
              className={`flex h-full flex-col rounded-[32px] border p-6 ${
                primaryPlan
                  ? "border-stone-300 bg-[rgba(249,245,238,0.9)] shadow-[0_24px_60px_-42px_rgba(15,23,42,0.16)]"
                  : "border-stone-200 bg-white"
              }`}
            >
              {plan.highlight ? (
                <span className="inline-flex w-fit rounded-full bg-stone-100 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-stone-600">
                  {plan.highlight}
                </span>
              ) : null}
              <p className="mt-6 text-sm font-semibold uppercase tracking-[0.18em] text-stone-500">
                {plan.name}
              </p>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="landing-v2-display text-4xl font-semibold text-slate-950">
                  {plan.price}
                </span>
                <span className="text-sm text-stone-500">{plan.period}</span>
              </div>
              <p className="mt-4 text-sm leading-7 text-stone-600">{plan.summary}</p>

              <div className="mt-6 space-y-3">
                {plan.features.map((feature) => (
                  <div key={feature} className="flex items-start gap-3 text-sm text-stone-700">
                    <div className="mt-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-stone-100 text-slate-700">
                      <Check className="h-3 w-3" />
                    </div>
                    <span>{feature}</span>
                  </div>
                ))}
              </div>

              <Link
                href={`/${locale}/auth/register`}
                className={`mt-8 inline-flex h-12 items-center justify-center gap-2 rounded-full text-sm font-semibold transition-colors duration-200 ${
                  primaryPlan
                    ? "bg-slate-900 text-white hover:bg-slate-800"
                    : "border border-stone-300 bg-white text-slate-900 hover:border-stone-400"
                }`}
              >
                {plan.cta}
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          )
        })}
      </div>

      {enterprisePlan ? (
        <div className="mt-5 rounded-[32px] border border-stone-200 bg-[rgba(248,244,238,0.7)] px-6 py-6">
          <div className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-center">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-stone-500">
                {enterprisePlan.name}
              </p>
              <p className="landing-v2-display mt-2 text-2xl font-semibold text-slate-950">
                {enterprisePlan.price}
              </p>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-stone-600">
                {enterprisePlan.summary}
              </p>
            </div>
            <Link
              href={`/${locale}/help`}
              className="inline-flex h-11 items-center justify-center rounded-full border border-stone-300 bg-white px-5 text-sm font-semibold text-slate-900 transition-colors duration-200 hover:border-stone-400"
            >
              {enterprisePlan.cta}
            </Link>
          </div>
        </div>
      ) : null}

      <div
        id="cta"
        className="mt-8 rounded-[36px] border border-stone-200 bg-[rgba(249,245,238,0.9)] p-6 sm:p-8"
      >
        <div className="grid gap-6 lg:grid-cols-[1fr_auto] lg:items-center">
          <div>
            <p className="landing-v2-display text-3xl font-semibold text-slate-950 sm:text-4xl">
              {t("cta.title")}
            </p>
            <p className="mt-4 max-w-2xl text-base leading-8 text-stone-600">
              {t("cta.subtitle")}
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row">
            <Link
              href={`/${locale}/auth/register`}
              className="inline-flex h-12 items-center justify-center rounded-full bg-slate-900 px-5 text-sm font-semibold text-white"
            >
              {t("cta.primary")}
            </Link>
            <Link
              href={`/${locale}/search`}
              className="inline-flex h-12 items-center justify-center rounded-full border border-stone-300 bg-white px-5 text-sm font-semibold text-slate-900"
            >
              {t("cta.secondary")}
            </Link>
          </div>
        </div>
      </div>
    </section>
  )
})
