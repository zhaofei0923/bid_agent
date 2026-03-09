"use client"

import Link from "next/link"
import { memo, useEffect, useState } from "react"
import { useTranslations } from "next-intl"
import { ArrowUpRight, Globe2 } from "lucide-react"

interface LandingV2NavProps {
  locale: string
}

export const LandingV2Nav = memo(function LandingV2Nav({
  locale,
}: LandingV2NavProps) {
  const t = useTranslations("landingV2")
  const altLocale = locale === "zh" ? "en" : "zh"
  const [isScrolled, setIsScrolled] = useState(false)
  const links = [
    { href: "#value", label: t("nav.platform") },
    { href: "#workflow", label: t("nav.workflow") },
  ]

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 16)
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  return (
    <header className="sticky top-0 z-50 px-6 py-4">
      <nav
        className={`mx-auto flex w-full max-w-[1320px] items-center justify-between rounded-full border px-4 py-3 transition-all duration-300 sm:px-6 ${
          isScrolled
            ? "border-stone-300/90 bg-[rgba(255,252,247,0.96)] shadow-[0_20px_44px_-30px_rgba(15,23,42,0.18)]"
            : "border-stone-200/70 bg-[rgba(255,252,247,0.86)]"
        }`}
      >
        <Link href={`/${locale}`} className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full border border-stone-300 bg-white text-[11px] font-semibold uppercase tracking-[0.26em] text-slate-700">
            BA
          </div>
          <p className="landing-v2-display text-lg font-semibold text-slate-900">
            BidAgent
          </p>
        </Link>

        <div className="hidden items-center gap-6 text-sm font-medium text-stone-600 lg:flex">
          {links.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="transition-colors duration-200 hover:text-slate-900"
            >
              {link.label}
            </a>
          ))}
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <Link
            href={`/${altLocale}`}
            className="hidden h-11 items-center gap-2 rounded-full border border-stone-300 bg-white px-4 text-sm font-medium text-stone-600 transition-colors duration-200 hover:text-slate-900 sm:flex"
          >
            <Globe2 className="h-4 w-4" />
            {locale === "zh" ? "EN" : "中文"}
          </Link>
          <Link
            href={`/${locale}/auth/login`}
            className="hidden h-11 items-center rounded-full px-4 text-sm font-medium text-stone-600 transition-colors duration-200 hover:text-slate-900 md:flex"
          >
            {t("nav.signIn")}
          </Link>
          <Link
            href={`/${locale}/auth/register`}
            className="inline-flex h-11 items-center gap-2 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white transition-colors duration-200 hover:bg-slate-800"
          >
            {t("nav.start")}
            <ArrowUpRight className="h-4 w-4" />
          </Link>
        </div>
      </nav>
    </header>
  )
})
