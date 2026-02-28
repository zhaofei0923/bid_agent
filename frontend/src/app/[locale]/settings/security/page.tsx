"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { useMutation } from "@tanstack/react-query"
import { authService } from "@/services/auth"

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
      <h2 className="text-lg font-semibold">{t("securityPage.title")}</h2>
      <p className="mt-1 text-sm text-gray-500">{t("securityPage.subtitle")}</p>

      {/* Change Password */}
      <div className="mt-6">
        <h3 className="font-medium">{t("securityPage.changePassword")}</h3>
        <div className="mt-4 max-w-md space-y-4">
          {error && (
            <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700">
              {t("securityPage.currentPassword")}
            </label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="mt-1 w-full rounded-lg border px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              {t("securityPage.newPassword")}
            </label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="mt-1 w-full rounded-lg border px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <p className="mt-1 text-xs text-gray-400">{t("securityPage.minChars")}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              {t("securityPage.confirmNewPassword")}
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="mt-1 w-full rounded-lg border px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleSubmit}
              disabled={changePasswordMutation.isPending}
              className="rounded-lg bg-blue-600 px-6 py-2 text-white hover:bg-blue-700 disabled:opacity-50 transition"
            >
              {changePasswordMutation.isPending ? t("securityPage.changingPassword") : t("securityPage.changePassword")}
            </button>
            {saved && (
              <span className="text-sm text-green-600">✓ {t("securityPage.passwordChanged")}</span>
            )}
          </div>
        </div>
      </div>

      {/* 2FA Section (placeholder) */}
      <div className="mt-8 border-t pt-6">
        <h3 className="font-medium">{t("securityPage.twoFA")}</h3>
        <p className="mt-1 text-sm text-gray-500">
          {t("securityPage.twoFADesc")}
        </p>
        <button
          disabled
          className="mt-4 rounded-lg border px-4 py-2 text-sm text-gray-400 cursor-not-allowed"
        >
          {tc("comingSoon")}
        </button>
      </div>

      {/* Sessions */}
      <div className="mt-8 border-t pt-6">
        <h3 className="font-medium">{t("securityPage.sessions")}</h3>
        <p className="mt-1 text-sm text-gray-500">{t("securityPage.sessionsDesc")}</p>
        <div className="mt-4 rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">{t("securityPage.currentDevice")}</p>
              <p className="text-xs text-gray-500">{t("securityPage.currentSession")}</p>
            </div>
            <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">
              {tc("active")}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
