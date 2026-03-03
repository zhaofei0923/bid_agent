import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-full text-sm font-semibold tracking-[-0.01em] ring-offset-background transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-400 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "bg-slate-900 text-white shadow-[0_18px_34px_-24px_rgba(15,23,42,0.55)] hover:-translate-y-0.5 hover:bg-slate-800",
        destructive:
          "bg-destructive text-destructive-foreground shadow-[0_16px_28px_-24px_rgba(220,38,38,0.7)] hover:-translate-y-0.5 hover:bg-destructive/90",
        outline:
          "border border-stone-300/90 bg-[rgba(255,255,255,0.92)] text-slate-700 shadow-[inset_0_1px_0_rgba(255,255,255,0.78)] hover:-translate-y-0.5 hover:border-stone-400 hover:bg-white hover:text-slate-900",
        secondary:
          "bg-stone-100 text-stone-700 shadow-[inset_0_1px_0_rgba(255,255,255,0.72)] hover:-translate-y-0.5 hover:bg-stone-200 hover:text-slate-900",
        ghost: "text-stone-600 hover:bg-stone-100 hover:text-slate-900",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-11 px-5 py-2.5",
        sm: "h-9 px-4 text-xs",
        lg: "h-12 px-6 text-base",
        icon: "h-10 w-10 rounded-2xl",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
