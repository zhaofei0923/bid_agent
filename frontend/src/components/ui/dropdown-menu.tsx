"use client"

import * as React from "react"

interface DropdownMenuContextValue {
  open: boolean
  setOpen: (open: boolean) => void
}

const DropdownContext = React.createContext<DropdownMenuContextValue>({
  open: false,
  setOpen: () => {},
})

export function DropdownMenu({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = React.useState(false)

  React.useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      if (!target.closest("[data-dropdown]")) setOpen(false)
    }
    document.addEventListener("click", handler)
    return () => document.removeEventListener("click", handler)
  }, [open])

  return (
    <DropdownContext.Provider value={{ open, setOpen }}>
      <div className="relative" data-dropdown>
        {children}
      </div>
    </DropdownContext.Provider>
  )
}

export function DropdownMenuTrigger({
  children,
  asChild,
}: {
  children: React.ReactNode
  asChild?: boolean
}) {
  const { open, setOpen } = React.useContext(DropdownContext)

  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children as React.ReactElement<{ onClick: () => void }>, {
      onClick: () => setOpen(!open),
    })
  }

  return (
    <button onClick={() => setOpen(!open)} type="button">
      {children}
    </button>
  )
}

export function DropdownMenuContent({
  children,
  align = "end",
  className = "",
}: {
  children: React.ReactNode
  align?: "start" | "end"
  className?: string
}) {
  const { open } = React.useContext(DropdownContext)
  if (!open) return null

  return (
    <div
      className={`absolute z-50 mt-2 min-w-[180px] rounded-lg border bg-white py-1 shadow-lg ${
        align === "end" ? "right-0" : "left-0"
      } ${className}`}
    >
      {children}
    </div>
  )
}

export function DropdownMenuItem({
  children,
  onClick,
  className = "",
  disabled = false,
}: {
  children: React.ReactNode
  onClick?: () => void
  className?: string
  disabled?: boolean
}) {
  const { setOpen } = React.useContext(DropdownContext)

  return (
    <button
      onClick={() => {
        if (disabled) return
        onClick?.()
        setOpen(false)
      }}
      disabled={disabled}
      className={`w-full px-3 py-2 text-left text-sm hover:bg-gray-100 disabled:opacity-50 ${className}`}
    >
      {children}
    </button>
  )
}

export function DropdownMenuSeparator() {
  return <div className="my-1 h-px bg-gray-200" />
}
