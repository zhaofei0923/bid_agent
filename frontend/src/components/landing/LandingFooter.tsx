"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useTranslations } from "next-intl"

export function LandingFooter() {
  const t = useTranslations("landing")
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"

  return (
    <footer className="py-12 bg-slate-900 text-white">
      <div className="container">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <span className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              BidAgent
            </span>
            <p className="mt-2 text-sm text-slate-400">
              {t("footerDesc")}
            </p>
          </div>

          <div>
            <h4 className="font-semibold mb-3 text-sm">{t("footerProduct")}</h4>
            <ul className="space-y-2 text-sm text-slate-400">
              <li><Link href={`/${locale}/search`} className="hover:text-white transition-colors">{t("footerBidSearch")}</Link></li>
              <li><a href="#features" className="hover:text-white transition-colors">{t("footerFeatures")}</a></li>
              <li><a href="#pricing" className="hover:text-white transition-colors">{t("footerPricing")}</a></li>
              <li><a href="#faq" className="hover:text-white transition-colors">FAQ</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-3 text-sm">{t("footerSupport")}</h4>
            <ul className="space-y-2 text-sm text-slate-400">
              <li><Link href="/help" className="hover:text-white transition-colors">{t("footerHelpCenter")}</Link></li>
              <li><a href="mailto:support@bidagent.ai" className="hover:text-white transition-colors">{t("footerContactUs")}</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-3 text-sm">{t("footerLegal")}</h4>
            <ul className="space-y-2 text-sm text-slate-400">
              <li><a href="#" className="hover:text-white transition-colors">{t("footerPrivacy")}</a></li>
              <li><a href="#" className="hover:text-white transition-colors">{t("footerTerms")}</a></li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-slate-800 text-center text-sm text-slate-500">
          &copy; {new Date().getFullYear()} BidAgent. All rights reserved.
        </div>
      </div>
    </footer>
  )
}
