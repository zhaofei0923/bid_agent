"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useTranslations } from "next-intl"

export function Footer() {
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"
  const t = useTranslations("nav")
  const tLanding = useTranslations("landingV2")
  const altLocale = locale === "zh" ? "en" : "zh"

  return (
    <footer className="border-t border-stone-200/90 pb-12 pt-10">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6">
        <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
          <div className="max-w-md">
            <p className="landing-v2-display text-2xl font-semibold text-slate-950">
              BidAgent
            </p>
            <p className="mt-3 text-sm leading-7 text-stone-600">
              {tLanding("footer.description")}
            </p>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <Link href={`/${locale}/dashboard`} className="text-sm text-stone-600 transition-colors duration-200 hover:text-slate-900">
              {t("dashboard")}
            </Link>
            <Link href={`/${locale}/opportunities`} className="text-sm text-stone-600 transition-colors duration-200 hover:text-slate-900">
              {t("opportunities")}
            </Link>
            <Link href={`/${locale}/projects`} className="text-sm text-stone-600 transition-colors duration-200 hover:text-slate-900">
              {t("projects")}
            </Link>
            <Link href={`/${locale}/help`} className="text-sm text-stone-600 transition-colors duration-200 hover:text-slate-900">
              {t("help")}
            </Link>
          </div>
        </div>
        <div className="flex flex-col gap-3 border-t border-stone-200 pt-5 text-xs uppercase tracking-[0.18em] text-stone-500 sm:flex-row sm:items-center sm:justify-between">
          <p>
          &copy; {new Date().getFullYear()} BidAgent. All rights reserved.
          </p>
          <Link
            href={`/${altLocale}`}
            className="transition-colors duration-200 hover:text-slate-900"
          >
            {locale === "zh" ? "EN" : "中文"}
          </Link>
        </div>
      </div>
    </footer>
  )
}
