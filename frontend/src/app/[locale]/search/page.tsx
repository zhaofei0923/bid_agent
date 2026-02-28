import type { Metadata } from "next"
import { getTranslations } from "next-intl/server"
import { LandingNav } from "@/components/landing/LandingNav"
import { LandingFooter } from "@/components/landing/LandingFooter"
import PublicSearchClient from "./PublicSearchClient"

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: "publicSearch" })
  return {
    title: `BidAgent — ${t("title")}`,
    description: t("subtitle"),
    keywords: [
      "ADB bidding",
      "World Bank bidding",
      "UN procurement",
      "tender search",
      "multilateral development bank",
    ],
  }
}

export default async function PublicSearchPage({
  params,
}: {
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params

  return (
    <div className="min-h-screen flex flex-col">
      <LandingNav />
      <main className="flex-1 pt-24 pb-16 bg-gray-50">
        <div className="container">
          <PublicSearchClient locale={locale} />
        </div>
      </main>
      <LandingFooter />
    </div>
  )
}
