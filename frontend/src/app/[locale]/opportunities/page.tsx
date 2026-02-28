"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { opportunityService } from "@/services/opportunities"
import { formatDate, formatCurrency, truncate } from "@/lib/utils"
import { MainLayout } from "@/components/layout/MainLayout"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Search, MapPin, Folder, Clock, DollarSign, Filter } from "lucide-react"
import type { OpportunitySearchParams } from "@/types"

export default function OpportunitiesPage() {
  const t = useTranslations("opportunities")
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"
  const [params, setParams] = useState<OpportunitySearchParams>({
    page: 1,
    page_size: 20,
  })
  const [searchText, setSearchText] = useState("")

  const { data, isLoading } = useQuery({
    queryKey: ["opportunities", params],
    queryFn: () => opportunityService.list(params),
  })

  const handleSearch = () => {
    setParams((p) => ({ ...p, search: searchText, page: 1 }))
  }

  return (
    <MainLayout>
      <main className="container mx-auto px-6 py-8">
        <h1 className="text-3xl font-bold tracking-tight">{t("title")}</h1>

        {/* Search Bar */}
        <div className="mt-8 flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="text"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder={t("search")}
              className="pl-10"
            />
          </div>
          <Button onClick={handleSearch} className="gap-2">
            <Filter className="h-4 w-4" />
            {t("filters")}
          </Button>
        </div>

        {/* Results */}
        {isLoading ? (
          <div className="mt-8 space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <Card key={i}>
                <CardContent className="p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <Skeleton className="h-5 w-12" />
                    <Skeleton className="h-4 w-24" />
                  </div>
                  <Skeleton className="h-6 w-3/4 mb-2" />
                  <Skeleton className="h-4 w-full mb-4" />
                  <div className="flex gap-4">
                    <Skeleton className="h-4 w-20" />
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-4 w-32" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="mt-8 space-y-4">
            {data?.items.length === 0 && (
              <Card className="border-dashed">
                <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                  <Search className="h-8 w-8 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{t("noResults")}</p>
                </CardContent>
              </Card>
            )}
            {data?.items.map((opp) => (
              <Link
                key={opp.id}
                href={`/${locale}/opportunities/${opp.id}`}
                className="block group"
              >
                <Card className="hover:shadow-md hover:border-blue-200 transition-all duration-200">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <Badge variant={opp.source === "adb" ? "default" : opp.source === "wb" ? "secondary" : "outline"} className="uppercase">
                            {opp.source}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {opp.project_number}
                          </span>
                        </div>
                        <h3 className="mt-3 text-lg font-semibold group-hover:text-blue-600 transition-colors">
                          {opp.title}
                        </h3>
                        {opp.description && (
                          <p className="mt-2 text-sm text-muted-foreground line-clamp-2">
                            {truncate(opp.description, 200)}
                          </p>
                        )}
                        <div className="mt-4 flex flex-wrap gap-4 text-sm text-muted-foreground">
                          {opp.country && (
                            <div className="flex items-center gap-1">
                              <MapPin className="h-4 w-4" />
                              <span>{opp.country}</span>
                            </div>
                          )}
                          {opp.sector && (
                            <div className="flex items-center gap-1">
                              <Folder className="h-4 w-4" />
                              <span>{opp.sector}</span>
                            </div>
                          )}
                          {opp.deadline && (
                            <div className="flex items-center gap-1">
                              <Clock className="h-4 w-4" />
                              <span>{formatDate(opp.deadline)}</span>
                            </div>
                          )}
                          {opp.budget_max && (
                            <div className="flex items-center gap-1">
                              <DollarSign className="h-4 w-4" />
                              <span>{formatCurrency(opp.budget_max, opp.currency || "USD")}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}

        {/* Pagination */}
        {data && data.total_pages > 1 && (
          <div className="mt-8 flex justify-center gap-2">
            {Array.from({ length: Math.min(data.total_pages, 10) }, (_, i) => (
              <Button
                key={i + 1}
                variant={params.page === i + 1 ? "default" : "outline"}
                size="sm"
                onClick={() => setParams((p) => ({ ...p, page: i + 1 }))}
              >
                {i + 1}
              </Button>
            ))}
          </div>
        )}
      </main>
    </MainLayout>
  )
}
