"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useLocale, useTranslations } from "next-intl"

const SETTINGS_NAV = [
  { key: "profile", icon: "👤" },
  { key: "credits", icon: "💰" },
  { key: "notifications", icon: "🔔" },
  { key: "security", icon: "🔒" },
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
    <div className="container mx-auto px-6 py-8">
      <h1 className="text-2xl font-bold">{t("title")}</h1>

      <div className="mt-6 flex gap-8">
        {/* Sidebar */}
        <nav className="w-56 shrink-0">
          <div className="space-y-1">
            {SETTINGS_NAV.map((item) => {
              const href = `/${locale}/settings/${item.key}`
              const isActive = pathname === href

              return (
                <Link
                  key={item.key}
                  href={href}
                  className={`flex items-center gap-3 rounded-lg px-4 py-2.5 text-sm transition ${
                    isActive
                      ? "bg-blue-50 text-blue-700 font-medium"
                      : "text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  <span>{item.icon}</span>
                  <span>{t(item.key) || item.key}</span>
                </Link>
              )
            })}
          </div>
        </nav>

        {/* Content */}
        <div className="flex-1">
          <div className="rounded-xl border bg-white p-6">{children}</div>
        </div>
      </div>
    </div>
  )
}
