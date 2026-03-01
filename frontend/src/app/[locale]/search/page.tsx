import type { Metadata } from "next"
import { getTranslations } from "next-intl/server"
import { LandingV2Nav } from "@/components/landing-v2/LandingV2Nav"
import { LandingV2Footer } from "@/components/landing-v2/LandingV2Footer"
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
    <div className="landing-v2-page landing-v2-body min-h-screen text-slate-900">
      <LandingV2Nav locale={locale} />
      <main className="flex-1 pb-16 pt-6">
        <div className="mx-auto w-full max-w-[1320px] px-6">
          <PublicSearchClient locale={locale} />
        </div>
      </main>
      <LandingV2Footer locale={locale} />
    </div>
  )
}
