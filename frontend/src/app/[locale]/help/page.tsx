"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { MainLayout } from "@/components/layout/MainLayout"

export default function HelpPage() {
  const t = useTranslations("help")
  const [openIndex, setOpenIndex] = useState<number | null>(null)

  const faqItems = t.raw("faqItems") as Array<{ q: string; a: string }>
  const guideItems = t.raw("guideItems") as Array<{ title: string; desc: string; icon: string }>

  return (
    <MainLayout>
      <div className="container mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold">{t("title")}</h1>
        <p className="mt-2 text-gray-600">
          {t("subtitle")}
        </p>

        {/* Search */}
        <div className="mt-6">
          <input
            type="text"
            placeholder={t("searchPlaceholder")}
            className="w-full max-w-lg rounded-lg border px-4 py-2.5 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {/* Guides */}
        <div className="mt-8">
          <h2 className="text-lg font-semibold">{t("guides")}</h2>
          <div className="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {guideItems.map((guide) => (
              <div
                key={guide.title}
                className="rounded-xl border p-6 hover:shadow-md transition cursor-pointer"
              >
                <span className="text-2xl">{guide.icon}</span>
                <h3 className="mt-3 font-semibold">{guide.title}</h3>
                <p className="mt-1 text-sm text-gray-500">{guide.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* FAQ */}
        <div className="mt-10">
          <h2 className="text-lg font-semibold">{t("faq")}</h2>
          <div className="mt-4 space-y-2">
            {faqItems.map((item, idx) => (
              <div key={idx} className="rounded-lg border bg-white">
                <button
                  onClick={() => setOpenIndex(openIndex === idx ? null : idx)}
                  className="flex w-full items-center justify-between p-4 text-left"
                >
                  <span className="font-medium">{item.q}</span>
                  <span
                    className={`text-gray-400 transition-transform ${
                      openIndex === idx ? "rotate-180" : ""
                    }`}
                  >
                    ▼
                  </span>
                </button>
                {openIndex === idx && (
                  <div className="border-t px-4 pb-4 pt-3 text-sm text-gray-600">
                    {item.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Contact */}
        <div className="mt-10 rounded-xl bg-gray-50 p-8 text-center">
          <h2 className="text-lg font-semibold">{t("moreQuestions")}</h2>
          <p className="mt-2 text-gray-600">
            {t("moreQuestionsDesc")}
          </p>
          <a
            href="mailto:support@bidagent.ai"
            className="mt-4 inline-block rounded-lg bg-blue-600 px-6 py-2 text-white hover:bg-blue-700 transition"
          >
            {t("contactSupport")}
          </a>
        </div>
      </div>
    </MainLayout>
  )
}
