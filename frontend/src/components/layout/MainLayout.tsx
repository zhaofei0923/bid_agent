"use client"

import type { ReactNode } from "react"
import { AuthProvider } from "@/components/providers/AuthProvider"
import { Header } from "@/components/layout/Header"
import { Footer } from "@/components/layout/Footer"

interface MainLayoutProps {
  children: ReactNode
  hideFooter?: boolean
  hideHeader?: boolean
}

export function MainLayout({
  children,
  hideFooter = false,
  hideHeader = false,
}: MainLayoutProps) {
  return (
    <AuthProvider>
      <div className="app-shell relative flex min-h-screen flex-col">
        {!hideHeader && <Header />}
        <div className="relative flex-1">{children}</div>
        {!hideFooter && <Footer />}
      </div>
    </AuthProvider>
  )
}
