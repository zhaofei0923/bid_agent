"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"

export function FAQSection() {
  const t = useTranslations("landing")
  const faqs = t.raw("landingFaqs") as Array<{ q: string; a: string }>
  const [openIndex, setOpenIndex] = useState<number | null>(1)

  return (
    <section id="faq" className="py-20 bg-muted/30">
      <div className="container">
        <h2 className="text-3xl font-bold text-center mb-12">{t("faqTitle")}</h2>
        <div className="max-w-3xl mx-auto space-y-2">
          {faqs.map((faq, i) => (
            <div key={i} className="rounded-lg border bg-background">
              <button
                onClick={() => setOpenIndex(openIndex === i ? null : i)}
                className="w-full flex items-center justify-between px-6 py-4 text-left"
              >
                <span className="text-sm font-medium">{faq.q}</span>
                <span className="text-muted-foreground ml-4 shrink-0">
                  {openIndex === i ? "−" : "+"}
                </span>
              </button>
              {openIndex === i && (
                <div className="px-6 pb-4">
                  <p className="text-sm text-muted-foreground">{faq.a}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
