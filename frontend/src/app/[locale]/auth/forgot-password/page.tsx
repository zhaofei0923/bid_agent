"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { usePathname } from "next/navigation"
import Link from "next/link"
import { authService } from "@/services/auth"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export default function ForgotPasswordPage() {
  const t = useTranslations("auth")
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"

  const [email, setEmail] = useState("")
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      await authService.forgotPassword(email)
      setSent(true)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(detail ?? "发送失败，请稍后重试")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="landing-v2-page landing-v2-body min-h-screen px-6 py-10 text-slate-900">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between">
        <Link href={`/${locale}`} className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-full border border-stone-300 bg-white text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-700">
            BA
          </div>
          <span className="landing-v2-display text-xl font-semibold">BidAgent</span>
        </Link>
        <Link
          href={`/${locale}/auth/login`}
          className="text-sm font-medium text-stone-600 transition-colors duration-200 hover:text-slate-900"
        >
          {t("backToLogin")}
        </Link>
      </div>

      <div className="mx-auto mt-20 w-full max-w-md">
        <section className="app-surface px-8 py-10">
          <p className="app-page-kicker">{t("forgotPassword")}</p>
          <h2 className="landing-v2-display mt-4 text-3xl font-semibold text-slate-900">
            {t("forgotPasswordTitle")}
          </h2>
          <p className="mt-3 text-sm leading-7 text-stone-600">
            {t("forgotPasswordDesc")}
          </p>

          {sent ? (
            <div className="mt-8 rounded-[22px] border border-emerald-200 bg-emerald-50 px-5 py-4 text-sm text-emerald-800">
              <p>{t("forgotPasswordSent")}</p>
              <Link
                href={`/${locale}/auth/login`}
                className="mt-3 inline-block font-semibold underline"
              >
                {t("backToLogin")} →
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="mt-8 space-y-5">
              {error && (
                <div className="rounded-[22px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {error}
                </div>
              )}
              <div>
                <label className="mb-2 block text-sm font-medium text-stone-700">
                  {t("email")}
                </label>
                <Input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                />
              </div>
              <Button type="submit" disabled={loading} className="w-full">
                {loading ? "..." : t("forgotPasswordButton")}
              </Button>
              <p className="text-center text-sm text-stone-500">
                <Link
                  href={`/${locale}/auth/login`}
                  className="font-medium text-slate-700 hover:text-slate-900"
                >
                  ← {t("backToLogin")}
                </Link>
              </p>
            </form>
          )}
        </section>
      </div>
    </div>
  )
}
