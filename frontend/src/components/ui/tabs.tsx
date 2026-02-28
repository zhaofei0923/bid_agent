"use client"

import * as React from "react"

interface TabsContextValue {
  value: string
  onValueChange: (value: string) => void
}

const TabsContext = React.createContext<TabsContextValue>({
  value: "",
  onValueChange: () => {},
})

export function Tabs({
  value,
  defaultValue,
  onValueChange,
  children,
  className = "",
}: {
  value?: string
  defaultValue?: string
  onValueChange?: (value: string) => void
  children: React.ReactNode
  className?: string
}) {
  const [internalValue, setInternalValue] = React.useState(defaultValue ?? "")
  const currentValue = value ?? internalValue
  const handleChange = onValueChange ?? setInternalValue

  return (
    <TabsContext.Provider value={{ value: currentValue, onValueChange: handleChange }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  )
}

export function TabsList({
  children,
  className = "",
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div
      className={`inline-flex items-center gap-1 rounded-lg bg-gray-100 p-1 ${className}`}
    >
      {children}
    </div>
  )
}

export function TabsTrigger({
  value,
  children,
  className = "",
}: {
  value: string
  children: React.ReactNode
  className?: string
}) {
  const ctx = React.useContext(TabsContext)
  const isActive = ctx.value === value

  return (
    <button
      onClick={() => ctx.onValueChange(value)}
      className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
        isActive
          ? "bg-white text-gray-900 shadow-sm"
          : "text-gray-600 hover:text-gray-900"
      } ${className}`}
    >
      {children}
    </button>
  )
}

export function TabsContent({
  value,
  children,
  className = "",
}: {
  value: string
  children: React.ReactNode
  className?: string
}) {
  const ctx = React.useContext(TabsContext)
  if (ctx.value !== value) return null
  return <div className={className}>{children}</div>
}
