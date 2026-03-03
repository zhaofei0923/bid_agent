"use client"

import { useState, useEffect, useRef } from "react"
import { useTranslations } from "next-intl"
import { useRouter, usePathname, useSearchParams } from "next/navigation"
import Link from "next/link"
import { useAuthStore } from "@/stores/auth"
import { authService } from "@/services/auth"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export default function VerifyEmailPage() {
  const t = useTranslations("auth")
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const locale = pathname.split("/")[1] || "zh"

  const email = searchParams.get("email") ?? ""
  const setTokens = useAuthStore((s) => s.setTokens)

  const [code, setCode] = useState(["", "", "", "", "", ""])
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [resending, setResending] = useState(false)
  const [resendCooldown, setResendCooldown] = useState(0)
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])

  // If no email in URL, redirect back to register
  useEffect(() => {
    if (!email) {
      router.replace(`/${locale}/auth/register`)
    }
  }, [email, locale, router])

  // Countdown timer for resend
  useEffect(() => {
    if (resendCooldown <= 0) return
    const timer = setInterval(() => {
      setResendCooldown((c) => {
        if (c <= 1) {
          clearInterval(timer)
          return 0
        }
        return c - 1
      })
    }, 1000)
    return () => clearInterval(timer)
  }, [resendCooldown])

  const handleCodeChange = (index: number, value: string) => {
    // Accept only digits
    const digit = value.replace(/\D/g, "").slice(-1)
    const next = [...code]
    next[index] = digit
    setCode(next)
    // Auto-focus next input
    if (digit && index < 5) {
      inputRefs.current[index + 1]?.focus()
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6)
    if (pasted.length === 6) {
      setCode(pasted.split(""))
      inputRefs.current[5]?.focus()
    }
    e.preventDefault()
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const fullCode = code.join("")
    if (fullCode.length < 6) {
      setError(t("verifyCodeRequired"))
      return
    }
    setError("")
    setLoading(true)
    try {
      const tokens = await authService.verifyEmail(email, fullCode)
      await setTokens(tokens)
      router.push(`/${locale}/dashboard`)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? t("verifyCodeError"))
    } finally {
      setLoading(false)
    }
  }

  const handleResend = async () => {
    if (resendCooldown > 0) return
    setResending(true)
    try {
      await authService.resendVerification(email)
      setResendCooldown(60)
      setError("")
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? t("resendError"))
    } finally {
      setResending(false)
    }
  }

  if (!email) return null

  const fullCode = code.join("")

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

      <div className="mx-auto mt-16 w-full max-w-md">
        <section className="app-surface px-8 py-10">
          {/* Mail icon */}
          <div className="mb-6 flex justify-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-slate-100">
              <svg
                className="h-8 w-8 text-slate-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"
                />
              </svg>
            </div>
          </div>

          <p className="app-page-kicker text-center">{t("verifyEmailLabel")}</p>
          <h2 className="landing-v2-display mt-3 text-center text-2xl font-semibold text-slate-900">
            {t("verifyEmailTitle")}
          </h2>
          <p className="mt-3 text-center text-sm leading-6 text-stone-500">
            {t("verifyEmailDesc")}{" "}
            <span className="font-medium text-slate-800">{email}</span>
          </p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-6">
            {error && (
              <div className="rounded-[22px] border border-red-200 bg-red-50 px-4 py-3 text-center text-sm text-red-700">
                {error}
              </div>
            )}

            {/* 6-digit code inputs */}
            <div
              className="flex items-center justify-center gap-2"
              onPaste={handlePaste}
            >
              {code.map((digit, i) => (
                <input
                  key={i}
                  ref={(el) => { inputRefs.current[i] = el }}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleCodeChange(i, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(i, e)}
                  className="h-14 w-11 rounded-xl border border-stone-200 bg-white text-center text-xl font-bold text-slate-900 shadow-sm outline-none ring-0 transition-all focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
                  aria-label={`验证码第 ${i + 1} 位`}
                  autoComplete="one-time-code"
                  autoFocus={i === 0}
                />
              ))}
            </div>

            <Button
              type="submit"
              disabled={loading || fullCode.length < 6}
              className="w-full"
            >
              {loading ? t("verifying") : t("verifyButton")}
            </Button>
          </form>

          {/* Resend */}
          <div className="mt-6 text-center text-sm text-stone-600">
            {t("noVerifyCode")}{" "}
            <button
              type="button"
              onClick={handleResend}
              disabled={resending || resendCooldown > 0}
              className="font-semibold text-slate-900 transition-colors hover:text-stone-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {resendCooldown > 0
                ? t("resendCooldown", { seconds: resendCooldown })
                : resending
                  ? "..."
                  : t("resendCode")}
            </button>
          </div>
        </section>
      </div>
    </div>
  )
}
