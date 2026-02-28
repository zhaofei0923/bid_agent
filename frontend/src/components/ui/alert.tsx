import * as React from "react"

const variants: Record<string, string> = {
  default: "bg-gray-50 border-gray-200 text-gray-800",
  destructive: "bg-red-50 border-red-200 text-red-800",
  success: "bg-green-50 border-green-200 text-green-800",
  warning: "bg-yellow-50 border-yellow-200 text-yellow-800",
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
    <div className={`rounded-lg border p-4 ${variants[variant]} ${className}`}>
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
