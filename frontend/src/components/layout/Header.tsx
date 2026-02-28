"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useTranslations } from "next-intl"
import { useAuthStore } from "@/stores/auth"
import { useCreditsBalance } from "@/hooks/use-credits"
import { Button } from "@/components/ui/button"

export function Header() {
  const t = useTranslations("nav")
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"
  const { user, isAuthenticated, logout } = useAuthStore()
  const { data: balance } = useCreditsBalance()

  const navItems = [
    { href: `/${locale}/dashboard`, label: t("dashboard") },
    { href: `/${locale}/opportunities`, label: t("opportunities") },
    { href: `/${locale}/projects`, label: t("projects") },
  ]

  return (
    <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <Link href={`/${locale}/dashboard`} className="mr-8 flex items-center gap-2">
          <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            BidAgent
          </span>
        </Link>

        <nav className="flex items-center gap-6 text-sm">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`transition-colors hover:text-foreground/80 ${
                pathname.startsWith(item.href)
                  ? "text-foreground font-medium"
                  : "text-foreground/60"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-4">
          {isAuthenticated && balance !== undefined && (
            <Link
              href={`/${locale}/settings/credits`}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              {balance} {t("credits")}
            </Link>
          )}

          <Link
            href={`/${locale === "zh" ? "en" : "zh"}${pathname.slice(3)}`}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            {locale === "zh" ? "EN" : "中文"}
          </Link>

          {isAuthenticated ? (
            <div className="flex items-center gap-3">
              <Link
                href={`/${locale}/settings/profile`}
                className="text-sm hover:text-foreground text-muted-foreground"
              >
                {user?.name || user?.email}
              </Link>
              <Button variant="ghost" size="sm" onClick={logout}>
                {t("logout")}
              </Button>
            </div>
          ) : (
            <Link href={`/${locale}/auth/login`}>
              <Button size="sm">{t("login")}</Button>
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}
