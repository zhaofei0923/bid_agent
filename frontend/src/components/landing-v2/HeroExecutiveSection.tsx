"use client"

import Link from "next/link"
import { memo } from "react"
import { useTranslations } from "next-intl"
import {
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  ListChecks,
} from "lucide-react"

interface HeroExecutiveSectionProps {
  locale: string
}

export const HeroExecutiveSection = memo(function HeroExecutiveSection({
  locale,
}: HeroExecutiveSectionProps) {
  const t = useTranslations("landingV2")
  const trustNotes = t.raw("hero.trustNotes") as string[]

  return (
    <section className="mx-auto w-full max-w-[1320px] px-6 pb-20 pt-10 sm:pb-24 sm:pt-14">
      <div className="grid gap-12 lg:grid-cols-[1fr_0.96fr] lg:items-center">
        <div>
          <p className="landing-v2-kicker">{t("hero.eyebrow")}</p>
          <h1 className="landing-v2-display mt-5 max-w-[11ch] text-5xl font-semibold leading-[1.02] text-slate-950 sm:text-6xl lg:text-7xl">
            {t("hero.title")}
          </h1>
          <p className="mt-6 max-w-2xl text-base leading-8 text-stone-600 sm:text-lg">
            {t("hero.subtitle")}
          </p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link
              href={`/${locale}/auth/register`}
              className="inline-flex h-14 items-center justify-center gap-2 rounded-full bg-slate-900 px-7 text-sm font-semibold text-white transition-colors duration-200 hover:bg-slate-800"
            >
              {t("hero.primaryCta")}
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href={`/${locale}/search`}
              className="inline-flex h-14 items-center justify-center gap-2 rounded-full border border-stone-300 bg-white px-7 text-sm font-semibold text-slate-900 transition-colors duration-200 hover:border-stone-400"
            >
              {t("hero.secondaryCta")}
              <ChevronRight className="h-4 w-4" />
            </Link>
          </div>

          <div className="mt-9 grid gap-3 sm:grid-cols-3">
            {trustNotes.map((note) => (
              <div
                key={note}
                className="flex items-start gap-3 rounded-3xl border border-stone-200 bg-white px-4 py-4 text-sm leading-6 text-stone-600 shadow-[0_18px_44px_-38px_rgba(15,23,42,0.14)]"
              >
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-slate-900" />
                <span>{note}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="relative">
          <div className="landing-v2-panel relative overflow-hidden p-6 sm:p-8">
            <div className="pointer-events-none absolute right-0 top-0 h-40 w-40 rounded-full bg-[radial-gradient(circle,rgba(15,23,42,0.05),transparent_68%)]" />

            <div className="landing-v2-card p-6 sm:p-7">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-stone-300" />
                <span className="h-2.5 w-2.5 rounded-full bg-stone-200" />
                <span className="h-2.5 w-2.5 rounded-full bg-stone-200" />
                <span className="ml-auto h-8 w-24 rounded-full bg-stone-100" />
              </div>
              <div className="mt-8 h-4 w-24 rounded-full bg-stone-100" />
              <div className="mt-4 h-6 w-4/5 rounded-full bg-stone-200" />
              <div className="mt-3 h-4 w-3/5 rounded-full bg-stone-100" />
              <div className="mt-7 grid gap-3 sm:grid-cols-2">
                <div className="rounded-3xl bg-stone-50 p-4">
                  <div className="h-3 w-20 rounded-full bg-stone-200" />
                  <div className="mt-3 h-5 w-16 rounded-full bg-stone-300" />
                </div>
                <div className="rounded-3xl bg-stone-50 p-4">
                  <div className="h-3 w-24 rounded-full bg-stone-200" />
                  <div className="mt-3 h-5 w-20 rounded-full bg-stone-300" />
                </div>
              </div>
            </div>

            <div className="mt-5 grid gap-4 sm:grid-cols-[0.92fr_1.08fr]">
              <div className="landing-v2-card p-5">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-stone-100 text-slate-700">
                  <ListChecks className="h-5 w-5" />
                </div>
                <div className="mt-5 space-y-4">
                  <div className="flex items-center gap-3">
                    <span className="h-2.5 w-2.5 rounded-full bg-slate-900" />
                    <span className="h-3 w-28 rounded-full bg-stone-200" />
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="h-2.5 w-2.5 rounded-full bg-stone-400" />
                    <span className="h-3 w-20 rounded-full bg-stone-200" />
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="h-2.5 w-2.5 rounded-full bg-stone-300" />
                    <span className="h-3 w-24 rounded-full bg-stone-200" />
                  </div>
                </div>
              </div>

              <div className="rounded-[28px] border border-stone-200 bg-[rgba(248,244,238,0.9)] p-5 shadow-[0_24px_56px_-42px_rgba(15,23,42,0.12)]">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white text-slate-700">
                  <ClipboardCheck className="h-5 w-5" />
                </div>
                <div className="mt-5 space-y-3">
                  <div className="rounded-3xl bg-white px-4 py-4">
                    <div className="h-3 w-24 rounded-full bg-stone-200" />
                    <div className="mt-3 h-3 w-full rounded-full bg-stone-100" />
                    <div className="mt-2 h-3 w-5/6 rounded-full bg-stone-100" />
                  </div>
                  <div className="rounded-3xl bg-white px-4 py-4">
                    <div className="h-3 w-16 rounded-full bg-stone-200" />
                    <div className="mt-3 h-3 w-4/5 rounded-full bg-stone-100" />
                    <div className="mt-2 h-3 w-3/5 rounded-full bg-stone-100" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
})
