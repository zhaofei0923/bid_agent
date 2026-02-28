"use client"

import { useEffect, type ReactNode } from "react"
import { useRouter, usePathname } from "next/navigation"
import { useAuthStore } from "@/stores/auth"
import { Skeleton } from "@/components/ui/skeleton"

const PUBLIC_PATHS = ["/auth/login", "/auth/register", "/help"]

function isPublicPath(pathname: string): boolean {
  if (pathname.match(/^\/[a-z]{2}$/)) return true // landing page /{locale}
  return PUBLIC_PATHS.some((p) => pathname.includes(p))
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading, loadUser } = useAuthStore()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    loadUser()
  }, [loadUser])

  useEffect(() => {
    if (!isLoading && !isAuthenticated && !isPublicPath(pathname)) {
      const locale = pathname.split("/")[1] || "zh"
      router.replace(`/${locale}/auth/login?redirect=${encodeURIComponent(pathname)}`)
    }
  }, [isAuthenticated, isLoading, pathname, router])

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="space-y-4 w-64">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      </div>
    )
  }

  return <>{children}</>
}
