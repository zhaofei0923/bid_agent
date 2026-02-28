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
      className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
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
