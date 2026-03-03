"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { MainLayout } from "@/components/layout/MainLayout"
import { AppPageShell } from "@/components/layout/AppPageShell"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export default function HelpPage() {
  const t = useTranslations("help")
  const [openIndex, setOpenIndex] = useState<number | null>(null)

  const faqItems = t.raw("faqItems") as Array<{ q: string; a: string }>
  const guideItems = t.raw("guideItems") as Array<{ title: string; desc: string; icon: string }>

  return (
    <MainLayout>
      <AppPageShell
        eyebrow={t("guides")}
        title={t("title")}
        description={t("subtitle")}
      >

        {/* Search */}
        <div className="app-section-frame px-6 py-6 sm:px-8">
          <Input
            type="text"
            placeholder={t("searchPlaceholder")}
            className="max-w-xl"
          />
        </div>

        {/* Guides */}
        <div>
          <h2 className="app-section-title">{t("guides")}</h2>
          <div className="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {guideItems.map((guide) => (
              <div
                key={guide.title}
                className="app-surface app-card-interactive cursor-pointer px-6 py-6"
              >
                <span className="text-2xl">{guide.icon}</span>
                <h3 className="mt-4 text-lg font-semibold text-slate-900">{guide.title}</h3>
                <p className="mt-2 text-sm leading-7 text-stone-600">{guide.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* FAQ */}
        <div>
          <h2 className="app-section-title">{t("faq")}</h2>
          <div className="mt-4 space-y-2">
            {faqItems.map((item, idx) => (
              <div key={idx} className="app-surface overflow-hidden rounded-[24px]">
                <button
                  onClick={() => setOpenIndex(openIndex === idx ? null : idx)}
                  className="flex w-full items-center justify-between px-5 py-4 text-left"
                >
                  <span className="font-medium text-slate-900">{item.q}</span>
                  <span
                    className={`text-stone-400 transition-transform ${
                      openIndex === idx ? "rotate-180" : ""
                    }`}
                  >
                    ▼
                  </span>
                </button>
                {openIndex === idx && (
                  <div className="border-t border-stone-200 px-5 pb-5 pt-4 text-sm leading-7 text-stone-600">
                    {item.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Contact */}
        <div className="app-section-frame px-6 py-8 text-center sm:px-8">
          <h2 className="app-section-title">{t("moreQuestions")}</h2>
          <p className="mx-auto mt-3 max-w-2xl text-sm leading-7 text-stone-600">
            {t("moreQuestionsDesc")}
          </p>
          <Button asChild className="mt-5">
            <a href="mailto:support@bidagent.ai">{t("contactSupport")}</a>
          </Button>
        </div>
      </AppPageShell>
    </MainLayout>
  )
}
