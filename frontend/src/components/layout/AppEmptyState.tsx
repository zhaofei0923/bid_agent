import type { ReactNode } from "react"

interface AppEmptyStateProps {
  title: string
  description?: string
  icon?: ReactNode
  action?: ReactNode
}

export function AppEmptyState({
  title,
  description,
  icon,
  action,
}: AppEmptyStateProps) {
  return (
    <div className="app-empty-state flex flex-col items-center justify-center px-6 py-12 text-center sm:px-8">
      {icon && (
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-stone-200 bg-stone-50 text-stone-600">
          {icon}
        </div>
      )}
      <p className="text-base font-semibold text-slate-900">{title}</p>
      {description && <p className="mt-2 max-w-xl text-sm leading-7 text-stone-600">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}
