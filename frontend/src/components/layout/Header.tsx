"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useTranslations } from "next-intl"
import { useAuthStore } from "@/stores/auth"
import { useCreditsBalance } from "@/hooks/use-credits"
import { ArrowUpRight, Globe2, ShieldCheck } from "lucide-react"

export function Header() {
  const t = useTranslations("nav")
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"
  const altLocale = locale === "zh" ? "en" : "zh"
  const { user, isAuthenticated, logout } = useAuthStore()
  const { data: balance } = useCreditsBalance()
  const [isScrolled, setIsScrolled] = useState(false)

  const navItems = useMemo(
    () => [
      { href: `/${locale}/dashboard`, label: t("dashboard") },
      { href: `/${locale}/opportunities`, label: t("opportunities") },
      { href: `/${locale}/projects`, label: t("projects") },
      { href: `/${locale}/help`, label: t("help") },
    ],
    [locale, t]
  )

  const altPath = pathname.replace(/^\/(zh|en)(?=\/|$)/, `/${altLocale}`) || `/${altLocale}`

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 16)
    handleScroll()
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  return (
    <header className="sticky top-0 z-50 px-4 py-4">
      <div
        className={`mx-auto flex max-w-6xl items-center gap-4 rounded-full border px-4 py-3 transition-all duration-300 sm:px-6 ${
          isScrolled
            ? "border-stone-300/90 bg-[rgba(255,252,247,0.96)] shadow-[0_20px_44px_-30px_rgba(15,23,42,0.18)]"
            : "border-stone-200/80 bg-[rgba(255,252,247,0.88)]"
        }`}
      >
        <Link href={`/${locale}`} className="mr-2 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full border border-stone-300 bg-white text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-700">
            BA
          </div>
          <span className="landing-v2-display text-lg font-semibold text-slate-900">
            BidAgent
          </span>
        </Link>

        <nav className="hidden items-center gap-6 text-sm font-medium text-stone-600 lg:flex">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`transition-colors duration-200 hover:text-slate-900 ${
                pathname.startsWith(item.href)
                  ? "text-slate-900"
                  : "text-stone-600"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-2 sm:gap-3">
          {isAuthenticated && balance !== undefined && (
            <Link
              href={`/${locale}/settings/credits`}
              className="hidden h-10 items-center rounded-full border border-stone-200 bg-white px-4 text-sm font-medium text-stone-600 transition-colors duration-200 hover:text-slate-900 sm:flex"
            >
              {balance} {t("credits")}
            </Link>
          )}

          {isAuthenticated && user?.role === "admin" && (
            <Link
              href={`/${locale}/admin`}
              className="hidden h-10 items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-4 text-sm font-medium text-amber-700 transition-colors duration-200 hover:bg-amber-100 md:flex"
            >
              <ShieldCheck className="h-3.5 w-3.5" />
              {t("adminPanel")}
            </Link>
          )}

          <Link
            href={altPath}
            className="hidden h-10 items-center gap-2 rounded-full border border-stone-300 bg-white px-4 text-sm font-medium text-stone-600 transition-colors duration-200 hover:text-slate-900 md:flex"
          >
            <Globe2 className="h-4 w-4" />
            {locale === "zh" ? "EN" : "中文"}
          </Link>

          {isAuthenticated ? (
            <div className="flex items-center gap-3">
              <Link
                href={`/${locale}/settings/profile`}
                className="hidden text-sm text-stone-600 transition-colors duration-200 hover:text-slate-900 md:block"
              >
                {user?.name || user?.email}
              </Link>
              <button
                type="button"
                onClick={logout}
                className="inline-flex h-10 items-center rounded-full border border-stone-300 bg-white px-4 text-sm font-medium text-stone-600 transition-colors duration-200 hover:text-slate-900"
              >
                {t("logout")}
              </button>
            </div>
          ) : (
            <Link
              href={`/${locale}/auth/login`}
              className="inline-flex h-10 items-center gap-2 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white transition-colors duration-200 hover:bg-slate-800"
            >
              {t("login")}
              <ArrowUpRight className="h-4 w-4" />
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}
