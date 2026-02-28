import type { Metadata } from "next"
import { getTranslations } from "next-intl/server"
import { LandingNav } from "@/components/landing/LandingNav"
import { HeroSection } from "@/components/landing/HeroSection"
import { TrustBar } from "@/components/landing/TrustBar"
import { PainPointsSection } from "@/components/landing/PainPointsSection"
import { FeaturesSection } from "@/components/landing/FeaturesSection"
import { WorkflowSection } from "@/components/landing/WorkflowSection"
import { ComparisonSection } from "@/components/landing/ComparisonSection"
import { PersonasSection } from "@/components/landing/PersonasSection"
import { StatsSection } from "@/components/landing/StatsSection"
import { PricingSection } from "@/components/landing/PricingSection"
import { FAQSection } from "@/components/landing/FAQSection"
import { CTASection } from "@/components/landing/CTASection"
import { LandingFooter } from "@/components/landing/LandingFooter"

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: "landing" })
  return {
    title: `BidAgent — ${t("heroTitle")}`,
    description: t("heroSubtitle", { institutions: "ADB/WB/UN" }),
    keywords: ["ADB bidding", "World Bank bidding", "UN procurement", "proposal writing", "AI bid assistant"],
  }
}

export default async function LandingPage({
  params,
}: {
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params

  return (
    <div className="min-h-screen">
      <LandingNav />
      <HeroSection locale={locale} />
      <TrustBar />
      <PainPointsSection />
      <FeaturesSection />
      <WorkflowSection />
      <ComparisonSection />
      <PersonasSection />
      <StatsSection />
      <PricingSection locale={locale} />
      <FAQSection />
      <CTASection locale={locale} />
      <LandingFooter />
    </div>
  )
}
