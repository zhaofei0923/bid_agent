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
        className="fixed inset-0 bg-[rgba(15,23,42,0.42)] backdrop-blur-[2px]"
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
      className={`relative z-50 w-full max-w-lg rounded-[28px] border border-stone-200/90 bg-[rgba(255,252,247,0.97)] p-6 shadow-[0_36px_90px_-44px_rgba(15,23,42,0.25)] ${className}`}
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
  return <div className={`mb-5 ${className}`}>{children}</div>
}

export function DialogTitle({
  children,
  className = "",
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <h2 className={`font-semibold tracking-[-0.02em] text-slate-900 sm:text-xl ${className}`}>
      {children}
    </h2>
  )
}

export function DialogDescription({
  children,
  className = "",
}: {
  children: React.ReactNode
  className?: string
}) {
  return <p className={`text-sm leading-7 text-stone-600 ${className}`}>{children}</p>
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
