"use client"

import { useEffect } from "react"
import { useRouter, usePathname } from "next/navigation"
import { useAuthStore } from "@/stores/auth"

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, isLoading } = useAuthStore()
  const router = useRouter()
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"

  useEffect(() => {
    if (!isLoading && (!isAuthenticated || user?.role !== "admin")) {
      router.replace(`/${locale}/dashboard`)
    }
  }, [isLoading, isAuthenticated, user, router, locale])

  if (isLoading || !isAuthenticated || user?.role !== "admin") {
    return null
  }

  return <>{children}</>
}
