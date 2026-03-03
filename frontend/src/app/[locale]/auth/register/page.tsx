"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { useRouter, usePathname } from "next/navigation"
import Link from "next/link"
import { useAuthStore } from "@/stores/auth"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export default function RegisterPage() {
  const t = useTranslations("auth")
  const tLanding = useTranslations("landingV2")
  const router = useRouter()
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"
  const register = useAuthStore((s) => s.register)

  const [form, setForm] = useState({
    email: "",
    password: "",
    name: "",
    company: "",
  })
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      const email = await register(form.email, form.password, form.name, form.company || undefined)
      router.push(`/${locale}/auth/verify-email?email=${encodeURIComponent(email)}`)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? t("registerError"))
    } finally {
      setLoading(false)
    }
  }

  const update = (field: string, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }))

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
          {t("loginButton")}
        </Link>
      </div>

      <div className="mx-auto mt-10 grid w-full max-w-6xl gap-8 lg:grid-cols-[1.05fr_0.95fr]">
        <section className="app-panel flex flex-col justify-between px-7 py-8 sm:px-10 sm:py-10">
          <div>
            <p className="app-page-kicker">{tLanding("pricing.label")}</p>
            <h1 className="landing-v2-display mt-5 text-4xl font-semibold leading-tight text-slate-900 sm:text-5xl">
              {tLanding("cta.title")}
            </h1>
            <p className="mt-5 max-w-xl text-base leading-8 text-stone-600 sm:text-lg">
              {tLanding("cta.subtitle")}
            </p>
          </div>
          <div className="mt-8 grid gap-4 sm:grid-cols-2">
            {tLanding.raw("pricing.plans").slice(0, 2).map((plan: { name: string; summary: string }) => (
              <div key={plan.name} className="app-surface-muted px-5 py-5">
                <p className="text-sm font-semibold text-slate-900">{plan.name}</p>
                <p className="mt-2 text-sm leading-7 text-stone-600">{plan.summary}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="app-surface px-6 py-8 sm:px-8 sm:py-10">
          <p className="app-page-kicker">{t("registerButton")}</p>
          <h2 className="landing-v2-display mt-4 text-3xl font-semibold text-slate-900">
            {t("registerTitle")}
          </h2>

          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            {error && (
              <div className="rounded-[22px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <div>
              <label className="mb-2 block text-sm font-medium text-stone-700">
                {t("name")}
              </label>
              <Input
                type="text"
                value={form.name}
                onChange={(e) => update("name", e.target.value)}
                required
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-stone-700">
                {t("email")}
              </label>
              <Input
                type="email"
                value={form.email}
                onChange={(e) => update("email", e.target.value)}
                required
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-stone-700">
                {t("password")}
              </label>
              <Input
                type="password"
                value={form.password}
                onChange={(e) => update("password", e.target.value)}
                required
                minLength={8}
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-stone-700">
                {t("company")}
              </label>
              <Input
                type="text"
                value={form.company}
                onChange={(e) => update("company", e.target.value)}
              />
            </div>

            <Button type="submit" disabled={loading} className="w-full">
              {loading ? "..." : t("registerButton")}
            </Button>
          </form>

          <p className="mt-6 text-sm text-stone-600">
            {t("hasAccount")}{" "}
            <Link
              href={`/${locale}/auth/login`}
              className="font-semibold text-slate-900 transition-colors duration-200 hover:text-stone-700"
            >
              {t("loginButton")}
            </Link>
          </p>
        </section>
      </div>
    </div>
  )
}
