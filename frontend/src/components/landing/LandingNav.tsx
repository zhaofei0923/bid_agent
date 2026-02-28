"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useTranslations } from "next-intl"
import { Button } from "@/components/ui/button"

export function LandingNav() {
  const t = useTranslations("landing")
  const [isScrolled, setIsScrolled] = useState(false)
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 50)
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? "bg-white/80 backdrop-blur-md shadow-sm border-b"
          : "bg-transparent"
      }`}
    >
      <div className="container flex h-16 items-center justify-between">
        <Link href={`/${locale}`} className="flex items-center gap-2">
          <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            BidAgent
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-6 text-sm">
          <Link href={`/${locale}/search`} className="text-muted-foreground hover:text-foreground transition-colors font-medium">
            {t("navSearch")}
          </Link>
          <a href="#features" className="text-muted-foreground hover:text-foreground transition-colors">
            {t("navFeatures")}
          </a>
          <a href="#pricing" className="text-muted-foreground hover:text-foreground transition-colors">
            {t("navPricing")}
          </a>
          <a href="#faq" className="text-muted-foreground hover:text-foreground transition-colors">
            FAQ
          </a>
        </div>

        <div className="flex items-center gap-3">
          <Link href={`/${locale === "zh" ? "en" : "zh"}`} className="text-sm text-muted-foreground hover:text-foreground">
            {locale === "zh" ? "EN" : "中文"}
          </Link>
          <Link href={`/${locale}/auth/login`}>
            <Button variant="ghost" size="sm">{t("navLogin")}</Button>
          </Link>
          <Link href={`/${locale}/auth/register`}>
            <Button size="sm">{t("navTrial")}</Button>
          </Link>
        </div>
      </div>
    </nav>
  )
}
