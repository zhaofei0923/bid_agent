"use client"

import * as React from "react"

export function Select({
  value,
  onValueChange,
  children,
}: {
  value?: string
  onValueChange?: (value: string) => void
  children: React.ReactNode
}) {
  return (
    <select
      value={value}
      onChange={(e) => onValueChange?.(e.target.value)}
      className="h-11 rounded-2xl border border-stone-300/90 bg-[rgba(255,255,255,0.92)] px-4 py-2 text-sm text-slate-900 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-stone-400 focus:ring-offset-2"
    >
      {children}
    </select>
  )
}

export function SelectOption({
  value,
  children,
}: {
  value: string
  children: React.ReactNode
}) {
  return <option value={value}>{children}</option>
}
