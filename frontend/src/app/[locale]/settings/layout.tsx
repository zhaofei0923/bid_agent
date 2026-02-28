"use client"

import { MainLayout } from "@/components/layout/MainLayout"
import SettingsLayout from "@/components/settings/SettingsLayout"

export default function SettingsPageLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <MainLayout>
      <SettingsLayout>{children}</SettingsLayout>
    </MainLayout>
  )
}
