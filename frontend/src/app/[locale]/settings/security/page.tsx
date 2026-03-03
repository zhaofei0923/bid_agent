"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { useMutation } from "@tanstack/react-query"
import { authService } from "@/services/auth"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export default function SecurityPage() {
  const t = useTranslations("settings")
  const tc = useTranslations("common")
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [error, setError] = useState("")
  const [saved, setSaved] = useState(false)

  const changePasswordMutation = useMutation({
    mutationFn: () =>
      authService.changePassword(currentPassword, newPassword),
    onSuccess: () => {
      setSaved(true)
      setCurrentPassword("")
      setNewPassword("")
      setConfirmPassword("")
      setError("")
      setTimeout(() => setSaved(false), 3000)
    },
    onError: () => {
      setError(t("securityPage.passwordError"))
    },
  })

  const handleSubmit = () => {
    setError("")
    if (newPassword.length < 8) {
      setError(t("securityPage.minChars"))
      return
    }
    if (newPassword !== confirmPassword) {
      setError(t("securityPage.passwordMismatch"))
      return
    }
    changePasswordMutation.mutate()
  }

  return (
    <div>
      <h2 className="app-section-title">{t("securityPage.title")}</h2>
      <p className="mt-2 text-sm leading-7 text-stone-600">{t("securityPage.subtitle")}</p>

      {/* Change Password */}
      <div className="app-section-frame mt-6 px-6 py-6">
        <h3 className="text-base font-semibold text-slate-900">{t("securityPage.changePassword")}</h3>
        <div className="mt-4 max-w-md space-y-4">
          {error && (
            <div className="rounded-[22px] border border-red-200 bg-red-50 p-3 text-sm text-red-600">
              {error}
            </div>
          )}

          <div>
            <label className="app-detail-label mb-2 block">
              {t("securityPage.currentPassword")}
            </label>
            <Input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
            />
          </div>

          <div>
            <label className="app-detail-label mb-2 block">
              {t("securityPage.newPassword")}
            </label>
            <Input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
            <p className="app-detail-label mt-2 text-stone-400">{t("securityPage.minChars")}</p>
          </div>

          <div>
            <label className="app-detail-label mb-2 block">
              {t("securityPage.confirmNewPassword")}
            </label>
            <Input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </div>

          <div className="flex items-center gap-3">
            <Button
              onClick={handleSubmit}
              disabled={changePasswordMutation.isPending}
            >
              {changePasswordMutation.isPending ? t("securityPage.changingPassword") : t("securityPage.changePassword")}
            </Button>
            {saved && (
              <span className="text-sm text-emerald-600">✓ {t("securityPage.passwordChanged")}</span>
            )}
          </div>
        </div>
      </div>

      {/* 2FA Section (placeholder) */}
      <div className="app-section-frame mt-6 px-6 py-6">
        <h3 className="text-base font-semibold text-slate-900">{t("securityPage.twoFA")}</h3>
        <p className="mt-2 text-sm leading-7 text-stone-600">
          {t("securityPage.twoFADesc")}
        </p>
        <Button disabled variant="outline" className="mt-4 cursor-not-allowed text-stone-400">
          {tc("comingSoon")}
        </Button>
      </div>

      {/* Sessions */}
      <div className="app-section-frame mt-6 px-6 py-6">
        <h3 className="text-base font-semibold text-slate-900">{t("securityPage.sessions")}</h3>
        <p className="mt-2 text-sm leading-7 text-stone-600">{t("securityPage.sessionsDesc")}</p>
        <div className="app-surface-muted mt-4 px-5 py-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-900">{t("securityPage.currentDevice")}</p>
              <p className="text-xs uppercase tracking-[0.12em] text-stone-500">{t("securityPage.currentSession")}</p>
            </div>
            <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-emerald-700">
              {tc("active")}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
