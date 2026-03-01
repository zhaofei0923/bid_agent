"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { useRouter, usePathname } from "next/navigation"
import Link from "next/link"
import { useAuthStore } from "@/stores/auth"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export default function LoginPage() {
  const t = useTranslations("auth")
  const tLanding = useTranslations("landingV2")
  const router = useRouter()
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"
  const login = useAuthStore((s) => s.login)

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      await login(email, password)
      router.push(`/${locale}/dashboard`)
    } catch {
      setError(t("loginError"))
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
          href={`/${locale}/auth/register`}
          className="text-sm font-medium text-stone-600 transition-colors duration-200 hover:text-slate-900"
        >
          {t("registerButton")}
        </Link>
      </div>

      <div className="mx-auto mt-10 grid w-full max-w-6xl gap-8 lg:grid-cols-[1.05fr_0.95fr]">
        <section className="app-panel flex flex-col justify-between px-7 py-8 sm:px-10 sm:py-10">
          <div>
            <p className="app-page-kicker">{tLanding("hero.eyebrow")}</p>
            <h1 className="landing-v2-display mt-5 text-4xl font-semibold leading-tight text-slate-900 sm:text-5xl">
              {tLanding("hero.title")}
            </h1>
            <p className="mt-5 max-w-xl text-base leading-8 text-stone-600 sm:text-lg">
              {tLanding("hero.subtitle")}
            </p>
          </div>
          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            {tLanding.raw("hero.trustNotes").map((note: string) => (
              <div key={note} className="app-surface-muted px-4 py-4">
                <p className="text-sm font-medium leading-7 text-stone-700">{note}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="app-surface px-6 py-8 sm:px-8 sm:py-10">
          <p className="app-page-kicker">{t("loginButton")}</p>
          <h2 className="landing-v2-display mt-4 text-3xl font-semibold text-slate-900">
            {t("loginTitle")}
          </h2>

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
                required
              />
            </div>

            <div>
              <div className="mb-2 flex items-center justify-between gap-3">
                <label className="block text-sm font-medium text-stone-700">
                  {t("password")}
                </label>
                <span className="text-xs font-medium uppercase tracking-[0.12em] text-stone-500">
                  {t("forgotPassword")}
                </span>
              </div>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <Button type="submit" disabled={loading} className="w-full">
              {loading ? "..." : t("loginButton")}
            </Button>
          </form>

          <p className="mt-6 text-sm text-stone-600">
            {t("noAccount")}{" "}
            <Link
              href={`/${locale}/auth/register`}
              className="font-semibold text-slate-900 transition-colors duration-200 hover:text-stone-700"
            >
              {t("registerButton")}
            </Link>
          </p>
        </section>
      </div>
    </div>
  )
}
