"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { useMutation } from "@tanstack/react-query"
import { useAuthStore } from "@/stores/auth"
import { authService } from "@/services/auth"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

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
      <h2 className="app-section-title">{t("profilePage.title")}</h2>
      <p className="mt-2 text-sm leading-7 text-stone-600">{t("profilePage.subtitle")}</p>

      <div className="mt-6 space-y-4">
        <div>
          <label className="mb-2 block text-sm font-medium text-stone-700">{t("profilePage.email")}</label>
          <Input
            type="email"
            value={user?.email ?? ""}
            disabled
            className="bg-stone-50 text-stone-500"
          />
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-stone-700">{t("profilePage.name")}</label>
          <Input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-stone-700">{t("profilePage.company")}</label>
          <Input
            type="text"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
          />
        </div>

        <div className="flex items-center gap-3">
          <Button
            onClick={() => updateMutation.mutate()}
            disabled={updateMutation.isPending}
          >
            {updateMutation.isPending ? tc("saving") : tc("save")}
          </Button>
          {saved && (
            <span className="text-sm text-emerald-600">✓ {tc("saveSuccess")}</span>
          )}
        </div>
      </div>
    </div>
  )
}
