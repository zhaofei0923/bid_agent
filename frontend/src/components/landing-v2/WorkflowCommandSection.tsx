"use client"

import { memo } from "react"
import { useTranslations } from "next-intl"
import { ArrowRight } from "lucide-react"
import { LandingV2WorkflowStep } from "./types"

export const WorkflowCommandSection = memo(function WorkflowCommandSection() {
  const t = useTranslations("landingV2")
  const steps = t.raw("workflow.steps") as LandingV2WorkflowStep[]

  return (
    <section id="workflow" className="mx-auto w-full max-w-[1320px] px-6 py-20">
      <div className="max-w-3xl">
        <p className="landing-v2-kicker">{t("workflow.label")}</p>
        <h2 className="landing-v2-display mt-4 text-3xl font-semibold text-slate-950 sm:text-4xl">
          {t("workflow.title")}
        </h2>
        <p className="mt-5 text-base leading-8 text-stone-600">
          {t("workflow.description")}
        </p>
      </div>

      <div className="relative mt-10">
        <div className="absolute left-14 right-14 top-8 hidden h-px bg-stone-200 lg:block" />
        <div className="grid gap-5 lg:grid-cols-3">
          {steps.map((step, index) => (
            <div key={step.name} className="landing-v2-card relative p-6">
              <div className="flex items-center justify-between">
                <div className="relative z-10 flex h-10 w-10 items-center justify-center rounded-full border border-stone-300 bg-white text-sm font-semibold text-slate-900">
                  0{index + 1}
                </div>
                <ArrowRight className="h-4 w-4 text-stone-400 lg:hidden" />
              </div>
              <h3 className="mt-6 text-xl font-semibold text-slate-950">{step.name}</h3>
              <p className="mt-3 text-sm leading-7 text-stone-600">{step.detail}</p>
              <div className="mt-6 rounded-3xl bg-stone-50 px-4 py-3 text-sm text-stone-700">
                {step.outcome}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
})
