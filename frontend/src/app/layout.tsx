import type { Metadata } from "next"
import { Noto_Serif_SC, Source_Sans_3 } from "next/font/google"
import "./globals.css"
import { Providers } from "./providers"

const notoSerifSc = Noto_Serif_SC({
  preload: false,
  display: "swap",
  weight: ["400", "500", "600", "700"],
  variable: "--font-heading",
})

const sourceSans = Source_Sans_3({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
  variable: "--font-ui",
})

export const metadata: Metadata = {
  title: "BidAgent - AI-Powered Bidding Platform",
  description:
    "AI-guided proposal writing platform for ADB, World Bank & UN bids",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html suppressHydrationWarning>
      <body className={`${sourceSans.className} ${sourceSans.variable} ${notoSerifSc.variable}`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
