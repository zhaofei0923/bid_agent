import * as React from "react"

export function Progress({
  value = 0,
  max = 100,
  className = "",
}: {
  value?: number
  max?: number
  className?: string
}) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100)

  return (
    <div className={`h-2 w-full overflow-hidden rounded-full bg-gray-100 ${className}`}>
      <div
        className="h-full rounded-full bg-blue-600 transition-all duration-300"
        style={{ width: `${percentage}%` }}
      />
    </div>
  )
}
