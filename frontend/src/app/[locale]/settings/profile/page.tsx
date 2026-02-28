"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { useMutation } from "@tanstack/react-query"
import { useAuthStore } from "@/stores/auth"
import { authService } from "@/services/auth"

export default function ProfilePage() {
  const t = useTranslations("settings")
  const tc = useTranslations("common")
  const user = useAuthStore((s) => s.user)

  const [name, setName] = useState(user?.name ?? "")
  const [company, setCompany] = useState(user?.company ?? "")
  const [saved, setSaved] = useState(false)

  const updateMutation = useMutation({
    mutationFn: () =>
      authService.updateMe({ name, company }),
    onSuccess: () => {
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    },
  })

  return (
    <div>
      <h2 className="text-lg font-semibold">{t("profilePage.title")}</h2>
      <p className="mt-1 text-sm text-gray-500">{t("profilePage.subtitle")}</p>

      <div className="mt-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">{t("profilePage.email")}</label>
          <input
            type="email"
            value={user?.email ?? ""}
            disabled
            className="mt-1 w-full rounded-lg border bg-gray-50 px-3 py-2 text-gray-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">{t("profilePage.name")}</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 w-full rounded-lg border px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">{t("profilePage.company")}</label>
          <input
            type="text"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            className="mt-1 w-full rounded-lg border px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => updateMutation.mutate()}
            disabled={updateMutation.isPending}
            className="rounded-lg bg-blue-600 px-6 py-2 text-white hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {updateMutation.isPending ? tc("saving") : tc("save")}
          </button>
          {saved && (
            <span className="text-sm text-green-600">✓ {tc("saveSuccess")}</span>
          )}
        </div>
      </div>
    </div>
  )
}
