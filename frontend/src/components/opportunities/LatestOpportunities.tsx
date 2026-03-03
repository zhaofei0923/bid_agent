"use client"

import Link from "next/link"
import { useTranslations } from "next-intl"
import { useLatestOpportunities } from "@/hooks/use-opportunities"
import OppCard from "@/components/opportunities/OppCard"
import { Button } from "@/components/ui/button"
import { Loader2, ArrowRight } from "lucide-react"

interface LatestOpportunitiesProps {
  locale: string
  /** How many items to display */
  limit?: number
  /** Filter by source (adb/wb) */
  source?: string
  /** Link mode for OppCard: external opens original URL, internal opens /opportunities/:id */
  linkMode?: "internal" | "external"
  /** Whether to show a "View all" button */
  showViewAll?: boolean
}

export function LatestOpportunities({
  locale,
  limit = 6,
  source,
  linkMode = "external",
  showViewAll = true,
}: LatestOpportunitiesProps) {
  const t = useTranslations("opportunities")
  const tc = useTranslations("common")
  const { data, isLoading, error } = useLatestOpportunities(limit, source)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error || !data || data.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        {tc("noData")}
      </p>
    )
  }

  return (
    <div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {data.map((opp) => (
          <OppCard key={opp.id} opportunity={opp} linkMode={linkMode} />
        ))}
      </div>

      {showViewAll && (
        <div className="mt-6 flex justify-center">
          <Link href={`/${locale}/opportunities`}>
            <Button variant="outline" className="gap-2">
              {t("viewAll")}
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      )}
    </div>
  )
}
