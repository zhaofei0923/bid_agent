"use client"

import Link from "next/link"
import { memo } from "react"
import { useTranslations } from "next-intl"
import {
  ArrowRight,
  Check,
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

            {/* 顶部大卡：标书分析概览 */}
            <div className="landing-v2-card p-6 sm:p-7">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-stone-400" />
                <span className="h-2.5 w-2.5 rounded-full bg-stone-300" />
                <span className="h-2.5 w-2.5 rounded-full bg-stone-200" />
                <span className="ml-auto flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1 text-[11px] font-medium text-amber-700 ring-1 ring-amber-200">
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
                  {t("hero.mockCard.analyzing")}
                </span>
              </div>

              <p className="mt-6 text-[11px] font-semibold uppercase tracking-[0.18em] text-stone-400">
                ADB · Loan 4231-IND
              </p>
              <p className="mt-2 text-base font-semibold text-slate-900">
                {t("hero.mockCard.projectTitle")}
              </p>
              <p className="mt-1.5 text-xs text-stone-500">Technical Assistance · India</p>

              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                <div className="rounded-2xl bg-amber-50 px-4 py-4 ring-1 ring-amber-100">
                  <p className="text-[11px] font-medium text-amber-700">{t("hero.mockCard.matchLabel")}</p>
                  <p className="mt-2 text-2xl font-bold text-amber-600">86%</p>
                  <p className="mt-0.5 text-[11px] text-amber-500">{t("hero.mockCard.recommendation")}</p>
                </div>
                <div className="rounded-2xl bg-stone-50 px-4 py-4 ring-1 ring-stone-100">
                  <p className="text-[11px] font-medium text-stone-500">{t("hero.mockCard.deadlineLabel")}</p>
                  <p className="mt-2 text-base font-semibold text-slate-800">2025·05·30</p>
                  <p className="mt-0.5 text-[11px] text-stone-400">{t("hero.mockCard.daysLeft")}</p>
                </div>
              </div>
            </div>

            <div className="mt-5 grid gap-4 sm:grid-cols-[0.92fr_1.08fr]">
              {/* 左下卡：准备清单 */}
              <div className="landing-v2-card p-5">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-stone-100 text-slate-700">
                    <ListChecks className="h-4 w-4" />
                  </div>
                  <span className="text-xs font-semibold text-slate-700">{t("hero.mockCard.checklistTitle")}</span>
                </div>
                <div className="mt-5 space-y-3.5">
                  <div className="flex items-center gap-3">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                      <Check className="h-3 w-3" />
                    </span>
                    <span className="text-xs text-slate-700">{t("hero.mockCard.checkItem1")}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-amber-100">
                      <span className="h-2 w-2 rounded-full bg-amber-500" />
                    </span>
                    <span className="text-xs text-slate-700">{t("hero.mockCard.checkItem2")}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-stone-100">
                      <span className="h-2 w-2 rounded-full bg-stone-300" />
                    </span>
                    <span className="text-xs text-stone-400">{t("hero.mockCard.checkItem3")}</span>
                  </div>
                </div>
              </div>

              {/* 右下卡：AI 要求提炼 */}
              <div className="rounded-[28px] border border-stone-200 bg-[rgba(248,244,238,0.9)] p-5 shadow-[0_24px_56px_-42px_rgba(15,23,42,0.12)]">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-slate-700">
                    <ClipboardCheck className="h-4 w-4" />
                  </div>
                  <span className="text-xs font-semibold text-slate-700">{t("hero.mockCard.requirementsTitle")}</span>
                </div>
                <div className="mt-5 space-y-3">
                  <div className="rounded-2xl bg-white px-4 py-3.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-semibold text-slate-700">{t("hero.mockCard.qualLabel")}</span>
                      <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700 ring-1 ring-emerald-100">
                        {t("hero.mockCard.passCount")}
                      </span>
                    </div>
                    <div className="mt-2.5 space-y-1.5">
                      <div className="h-2.5 w-full rounded-full bg-stone-100" />
                      <div className="h-2.5 w-4/5 rounded-full bg-stone-100" />
                    </div>
                  </div>
                  <div className="rounded-2xl bg-white px-4 py-3.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-semibold text-slate-700">{t("hero.mockCard.riskLabel")}</span>
                      <span className="rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-700 ring-1 ring-amber-100">
                        {t("hero.mockCard.pendingCount")}
                      </span>
                    </div>
                    <div className="mt-2.5 space-y-1.5">
                      <div className="h-2.5 w-5/6 rounded-full bg-stone-100" />
                      <div className="h-2.5 w-3/5 rounded-full bg-stone-100" />
                    </div>
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
