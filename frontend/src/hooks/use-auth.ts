"use client"

import { useEffect } from "react"
import { useAuthStore } from "@/stores/auth"

export function useAuth() {
  const store = useAuthStore()

  useEffect(() => {
    store.loadUser()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return store
}
