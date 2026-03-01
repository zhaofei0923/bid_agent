"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"

interface NotificationSettings {
  email_opportunity: boolean
  email_deadline: boolean
  email_credits: boolean
  browser_push: boolean
}

export default function NotificationsPage() {
  const t = useTranslations("settings")
  const tc = useTranslations("common")
  const [settings, setSettings] = useState<NotificationSettings>({
    email_opportunity: true,
    email_deadline: true,
    email_credits: true,
    browser_push: false,
  })
  const [saved, setSaved] = useState(false)

  const toggle = (key: keyof NotificationSettings) => {
    setSettings((s) => ({ ...s, [key]: !s[key] }))
  }

  const handleSave = () => {
    // TODO: call API to save notification settings
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  const ITEMS: { key: keyof NotificationSettings; label: string; desc: string }[] = [
    {
      key: "email_opportunity",
      label: t("notificationsPage.newOpportunity"),
      desc: t("notificationsPage.newOpportunityDesc"),
    },
    {
      key: "email_deadline",
      label: t("notificationsPage.deadlineReminder"),
      desc: t("notificationsPage.deadlineReminderDesc"),
    },
    {
      key: "email_credits",
      label: t("notificationsPage.creditsAlert"),
      desc: t("notificationsPage.creditsAlertDesc"),
    },
    {
      key: "browser_push",
      label: t("notificationsPage.browserPush"),
      desc: t("notificationsPage.browserPushDesc"),
    },
  ]

  return (
    <div>
      <h2 className="app-section-title">{t("notificationsPage.title")}</h2>
      <p className="mt-2 text-sm leading-7 text-stone-600">{t("notificationsPage.subtitle")}</p>

      <div className="mt-6 space-y-4">
        {ITEMS.map((item) => (
          <div
            key={item.key}
            className="app-surface-muted flex items-center justify-between px-5 py-4"
          >
            <div>
              <p className="font-medium text-slate-900">{item.label}</p>
              <p className="text-sm leading-7 text-stone-600">{item.desc}</p>
            </div>
            <button
              onClick={() => toggle(item.key)}
              className={`relative h-6 w-11 rounded-full transition ${
                settings[item.key] ? "bg-slate-900" : "bg-stone-300"
              }`}
            >
              <span
                className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
                  settings[item.key] ? "translate-x-5" : "translate-x-0.5"
                }`}
              />
            </button>
          </div>
        ))}
      </div>

      <div className="mt-6 flex items-center gap-3">
        <button
          onClick={handleSave}
          className="inline-flex h-11 items-center rounded-full bg-slate-900 px-6 text-sm font-semibold text-white transition-colors duration-200 hover:bg-slate-800"
        >
          {t("notificationsPage.saveSettings")}
        </button>
        {saved && (
          <span className="text-sm text-emerald-600">✓ {tc("saveSuccess")}</span>
        )}
      </div>
    </div>
  )
}
