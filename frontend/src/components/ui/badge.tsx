import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] transition-colors focus:outline-none focus:ring-2 focus:ring-stone-400 focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-slate-900 text-white hover:bg-slate-800",
        secondary:
          "border-transparent bg-stone-100 text-stone-700 shadow-[inset_0_1px_0_rgba(255,255,255,0.7)] hover:bg-stone-200",
        destructive:
          "border-transparent bg-red-50 text-red-700 hover:bg-red-100",
        outline: "border-stone-300/90 bg-white/92 text-stone-600",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
