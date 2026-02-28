import type { Metadata } from "next"
import type { CSSProperties } from "react"
import { Noto_Serif_SC, Source_Sans_3 } from "next/font/google"
import { getTranslations } from "next-intl/server"
import { CapabilitiesSection } from "@/components/landing-v2/CapabilitiesSection"
import { CoverageTrustSection } from "@/components/landing-v2/CoverageTrustSection"
import { HeroExecutiveSection } from "@/components/landing-v2/HeroExecutiveSection"
import { LandingV2Footer } from "@/components/landing-v2/LandingV2Footer"
import { LandingV2Nav } from "@/components/landing-v2/LandingV2Nav"
import { ManagerOutcomesSection } from "@/components/landing-v2/ManagerOutcomesSection"
import { PricingV2Section } from "@/components/landing-v2/PricingV2Section"
import { RoleValidationSection } from "@/components/landing-v2/RoleValidationSection"
import { WorkflowCommandSection } from "@/components/landing-v2/WorkflowCommandSection"

const notoSerifSc = Noto_Serif_SC({
  preload: false,
  display: "swap",
  weight: ["400", "500", "600", "700"],
})

const sourceSans = Source_Sans_3({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
})

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: "landingV2" })

  return {
    title: t("metaTitle"),
    description: t("metaDescription"),
  }
}

export default async function LandingPage({
  params,
}: {
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params
  const fontVars = {
    "--font-heading": notoSerifSc.style.fontFamily,
    "--font-ui": sourceSans.style.fontFamily,
  } as CSSProperties

  return (
    <div
      className="landing-v2-page landing-v2-body min-h-screen overflow-x-hidden text-slate-900"
      style={fontVars}
    >
      <script
        async
        src="https://mcp.figma.com/mcp/html-to-design/capture.js"
      />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[440px] bg-[radial-gradient(circle_at_top_right,rgba(15,23,42,0.05),transparent_42%)]" />
      <div className="pointer-events-none absolute left-[-8%] top-[10rem] h-72 w-72 rounded-full bg-[radial-gradient(circle,rgba(215,204,186,0.32),transparent_70%)]" />
      <div className="relative">
        <LandingV2Nav locale={locale} />
        <main>
          <HeroExecutiveSection locale={locale} />
          <CoverageTrustSection />
          <ManagerOutcomesSection />
          <WorkflowCommandSection />
          <CapabilitiesSection />
          <RoleValidationSection />
          <PricingV2Section locale={locale} />
        </main>
        <LandingV2Footer locale={locale} />
      </div>
    </div>
  )
}
