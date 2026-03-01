"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useLocale, useTranslations } from "next-intl"
import { Bell, Coins, LockKeyhole, User } from "lucide-react"

const SETTINGS_NAV = [
  { key: "profile", icon: User },
  { key: "credits", icon: Coins },
  { key: "notifications", icon: Bell },
  { key: "security", icon: LockKeyhole },
] as const

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const locale = useLocale()
  const pathname = usePathname()
  const t = useTranslations("settings")

  return (
    <div className="app-page-wrap">
      <div className="app-panel px-6 py-8 sm:px-8">
        <p className="app-page-kicker">{t("title")}</p>
        <h1 className="app-page-title mt-4">{t("title")}</h1>
      </div>

      <div className="mt-8 flex flex-col gap-6 lg:flex-row">
        {/* Sidebar */}
        <nav className="app-surface w-full shrink-0 px-4 py-4 lg:w-72">
          <div className="space-y-1">
            {SETTINGS_NAV.map((item) => {
              const href = `/${locale}/settings/${item.key}`
              const isActive = pathname === href
              const Icon = item.icon

              return (
                <Link
                  key={item.key}
                  href={href}
                  className={`flex items-center gap-3 rounded-2xl px-4 py-3 text-sm transition ${
                    isActive
                      ? "bg-slate-900 text-white font-medium"
                      : "text-stone-600 hover:bg-stone-100"
                  }`}
                >
                  <span className="flex h-8 w-8 items-center justify-center rounded-2xl bg-white/80">
                    <Icon className="h-4 w-4" />
                  </span>
                  <span>{t(item.key) || item.key}</span>
                </Link>
              )
            })}
          </div>
        </nav>

        {/* Content */}
        <div className="flex-1">
          <div className="app-surface px-6 py-6 sm:px-8">{children}</div>
        </div>
      </div>
    </div>
  )
}
