"use client"

import * as React from "react"

interface DialogProps {
  open?: boolean
  onOpenChange?: (open: boolean) => void
  children: React.ReactNode
}

export function Dialog({ open, onOpenChange, children }: DialogProps) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50">
      <div
        className="fixed inset-0 bg-black/50"
        onClick={() => onOpenChange?.(false)}
      />
      <div className="fixed inset-0 flex items-center justify-center p-4">
        {children}
      </div>
    </div>
  )
}

export function DialogContent({
  children,
  className = "",
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div
      className={`relative z-50 w-full max-w-lg rounded-xl bg-white p-6 shadow-xl ${className}`}
    >
      {children}
    </div>
  )
}

export function DialogHeader({
  children,
  className = "",
}: {
  children: React.ReactNode
  className?: string
}) {
  return <div className={`mb-4 ${className}`}>{children}</div>
}

export function DialogTitle({
  children,
  className = "",
}: {
  children: React.ReactNode
  className?: string
}) {
  return <h2 className={`text-lg font-semibold ${className}`}>{children}</h2>
}

export function DialogDescription({
  children,
  className = "",
}: {
  children: React.ReactNode
  className?: string
}) {
  return <p className={`text-sm text-gray-500 ${className}`}>{children}</p>
}

export function DialogFooter({
  children,
  className = "",
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={`mt-6 flex justify-end gap-2 ${className}`}>{children}</div>
  )
}
