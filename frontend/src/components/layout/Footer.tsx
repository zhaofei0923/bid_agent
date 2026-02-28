"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

export function Footer() {
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"

  return (
    <footer className="border-t py-6 md:py-0">
      <div className="container flex flex-col items-center justify-between gap-4 md:h-16 md:flex-row">
        <p className="text-sm text-muted-foreground">
          &copy; {new Date().getFullYear()} BidAgent. All rights reserved.
        </p>
        <div className="flex gap-4 text-sm text-muted-foreground">
          <Link href={`/${locale}/help`} className="hover:text-foreground">
            Help
          </Link>
          <Link href="#" className="hover:text-foreground">
            Privacy
          </Link>
          <Link href="#" className="hover:text-foreground">
            Terms
          </Link>
        </div>
      </div>
    </footer>
  )
}
