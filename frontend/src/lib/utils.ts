import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import { format, formatDistanceToNow } from "date-fns"
import { zhCN, enUS } from "date-fns/locale"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date, locale: string = "zh") {
  return format(new Date(date), "yyyy-MM-dd", {
    locale: locale === "zh" ? zhCN : enUS,
  })
}

export function formatDateTime(date: string | Date, locale: string = "zh") {
  return format(new Date(date), "yyyy-MM-dd HH:mm", {
    locale: locale === "zh" ? zhCN : enUS,
  })
}

export function formatRelative(date: string | Date, locale: string = "zh") {
  return formatDistanceToNow(new Date(date), {
    addSuffix: true,
    locale: locale === "zh" ? zhCN : enUS,
  })
}

export function formatCurrency(
  amount: number,
  currency: string = "USD"
): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

export function formatCredits(amount: number): string {
  return new Intl.NumberFormat().format(amount)
}

export function truncate(str: string, maxLength: number = 100): string {
  if (str.length <= maxLength) return str
  return str.slice(0, maxLength) + "..."
}
