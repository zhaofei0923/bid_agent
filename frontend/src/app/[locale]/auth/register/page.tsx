"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { useRouter, usePathname } from "next/navigation"
import Link from "next/link"
import { useAuthStore } from "@/stores/auth"

export default function RegisterPage() {
  const t = useTranslations("auth")
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
      await register(form.email, form.password, form.name, form.company || undefined)
      router.push(`/${locale}/dashboard`)
    } catch {
      setError(t("registerError"))
    } finally {
      setLoading(false)
    }
  }

  const update = (field: string, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }))

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md rounded-xl bg-white p-8 shadow-lg">
        <h1 className="text-2xl font-bold text-center">{t("registerTitle")}</h1>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          {error && (
            <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700">
              {t("name")}
            </label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => update("name", e.target.value)}
              required
              className="mt-1 w-full rounded-lg border px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              {t("email")}
            </label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => update("email", e.target.value)}
              required
              className="mt-1 w-full rounded-lg border px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              {t("password")}
            </label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => update("password", e.target.value)}
              required
              minLength={8}
              className="mt-1 w-full rounded-lg border px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              {t("company")}
            </label>
            <input
              type="text"
              value={form.company}
              onChange={(e) => update("company", e.target.value)}
              className="mt-1 w-full rounded-lg border px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 py-2 text-white font-medium hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {loading ? "..." : t("registerButton")}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-500">
          {t("hasAccount")}{" "}
          <Link
            href={`/${locale}/auth/login`}
            className="text-blue-600 hover:underline"
          >
            {t("loginButton")}
          </Link>
        </p>
      </div>
    </div>
  )
}
