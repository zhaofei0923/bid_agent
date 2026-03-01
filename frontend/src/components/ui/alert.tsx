import * as React from "react"

const variants: Record<string, string> = {
  default: "bg-[rgba(255,255,255,0.94)] border-stone-200 text-slate-800",
  destructive: "bg-red-50 border-red-200 text-red-800",
  success: "bg-emerald-50 border-emerald-200 text-emerald-800",
  warning: "bg-amber-50 border-amber-200 text-amber-800",
}

export function Alert({
  variant = "default",
  children,
  className = "",
}: {
  variant?: "default" | "destructive" | "success" | "warning"
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={`rounded-[24px] border p-4 shadow-[0_16px_40px_-34px_rgba(15,23,42,0.2)] ${variants[variant]} ${className}`}>
      {children}
    </div>
  )
}

export function AlertTitle({
  children,
  className = "",
}: {
  children: React.ReactNode
  className?: string
}) {
  return <h5 className={`mb-1 font-medium ${className}`}>{children}</h5>
}

export function AlertDescription({
  children,
  className = "",
}: {
  children: React.ReactNode
  className?: string
}) {
  return <p className={`text-sm ${className}`}>{children}</p>
}
