import { LandingV2Footer } from "@/components/landing-v2/LandingV2Footer"
import { LandingV2Nav } from "@/components/landing-v2/LandingV2Nav"

export default async function DesignPreviewLayout({
  children,
  params,
}: {
  children: React.ReactNode
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params

  return (
    <div className="landing-v2-page landing-v2-body min-h-screen text-slate-900">
      <script
        async
        src="https://mcp.figma.com/mcp/html-to-design/capture.js"
      />
      <LandingV2Nav locale={locale} />
      <main className="mx-auto w-full max-w-[1320px] space-y-10 px-6 pb-24 pt-6">
        {children}
      </main>
      <LandingV2Footer locale={locale} />
    </div>
  )
}
