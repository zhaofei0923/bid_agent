import type { ReactNode } from "react"
import { cn } from "@/lib/utils"

interface AppPageShellProps {
  title: string
  children: ReactNode
  actions?: ReactNode
  description?: string
  eyebrow?: string
  wide?: boolean
  className?: string
  contentClassName?: string
}

export function AppPageShell({
  title,
  children,
  actions,
  description,
  eyebrow,
  wide = false,
  className,
  contentClassName,
}: AppPageShellProps) {
  return (
    <section className={cn("app-page-wrap", wide && "app-page-wrap--wide", className)}>
      <div className="app-panel px-6 py-8 sm:px-8 sm:py-10">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            {eyebrow && <p className="app-page-kicker">{eyebrow}</p>}
            <h1 className={cn("app-page-title", eyebrow && "mt-4")}>{title}</h1>
            {description && <p className="app-page-subtitle mt-4 max-w-2xl">{description}</p>}
          </div>
          {actions && <div className="flex flex-wrap items-center gap-3">{actions}</div>}
        </div>
      </div>
      <div className={cn("mt-8 space-y-8", contentClassName)}>{children}</div>
    </section>
  )
}
