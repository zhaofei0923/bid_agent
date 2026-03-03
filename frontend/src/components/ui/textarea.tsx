import * as React from "react"

import { cn } from "@/lib/utils"

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement> & { className?: string }
>(({ className = "", ...props }, ref) => {
  return (
    <textarea
      ref={ref}
      className={cn(
        "flex min-h-[112px] w-full rounded-[24px] border border-stone-300/90 bg-[rgba(255,255,255,0.94)] px-4 py-3 text-sm text-slate-900 shadow-[inset_0_1px_0_rgba(255,255,255,0.76)] placeholder:text-stone-400 transition-all duration-200 focus:border-stone-400 focus:outline-none focus:ring-2 focus:ring-stone-400 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    />
  )
})

Textarea.displayName = "Textarea"
