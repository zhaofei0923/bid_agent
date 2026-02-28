"use client"

import Link from "next/link"
import { memo } from "react"
import { useTranslations } from "next-intl"

interface LandingV2FooterProps {
  locale: string
}

export const LandingV2Footer = memo(function LandingV2Footer({
  locale,
}: LandingV2FooterProps) {
  const t = useTranslations("landingV2")
  const altLocale = locale === "zh" ? "en" : "zh"

  const groups = [
    {
      title: t("footer.productTitle"),
      items: [
        { label: t("footer.productOverview"), href: "#value" },
        { label: t("footer.productSearch"), href: `/${locale}/search` },
        { label: t("footer.productWorkflow"), href: "#workflow" },
      ],
    },
    {
      title: t("footer.supportTitle"),
      items: [
        { label: t("footer.supportHelp"), href: `/${locale}/help` },
        { label: t("footer.supportPricing"), href: "#pricing" },
      ],
    },
    {
      title: t("footer.companyTitle"),
      items: [
        { label: t("footer.companyAbout"), href: `/${locale}` },
        { label: t("footer.companyContact"), href: "#cta" },
        { label: t("footer.companyLanguage"), href: `/${altLocale}/home-v2-preview` },
      ],
    },
  ]

  return (
    <footer className="border-t border-stone-200 pb-14 pt-12">
      <div className="mx-auto grid w-full max-w-[1320px] gap-10 px-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div>
          <p className="landing-v2-display text-2xl font-semibold text-slate-950">
            BidAgent
          </p>
          <p className="mt-4 max-w-md text-sm leading-7 text-stone-600">
            {t("footer.description")}
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-3">
          {groups.map((group) => (
            <div key={group.title}>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-500">
                {group.title}
              </p>
              <div className="mt-4 space-y-3">
                {group.items.map((item) => (
                  <Link
                    key={item.label}
                    href={item.href}
                    className="block text-sm text-stone-600 transition-colors duration-200 hover:text-slate-900"
                  >
                    {item.label}
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mx-auto mt-10 flex w-full max-w-[1320px] flex-col gap-3 border-t border-stone-200 px-6 pt-6 text-xs uppercase tracking-[0.18em] text-stone-500 sm:flex-row sm:items-center sm:justify-between">
        <span>{t("footer.copyright")}</span>
        <Link
          href={`/${altLocale}/home-v2-preview`}
          className="transition-colors duration-200 hover:text-slate-900"
        >
          {t("footer.companyLanguage")}
        </Link>
      </div>
    </footer>
  )
})
