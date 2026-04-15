"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { opportunityService } from "@/services/opportunities"
import { formatDate, formatCurrency, truncate } from "@/lib/utils"
import { MainLayout } from "@/components/layout/MainLayout"
import { AppPageShell } from "@/components/layout/AppPageShell"
import { AppEmptyState } from "@/components/layout/AppEmptyState"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Search, MapPin, Folder, Clock, DollarSign, Filter } from "lucide-react"
import type { OpportunitySearchParams } from "@/types"

export default function OpportunitiesPage() {
  const t = useTranslations("opportunities")
  const tc = useTranslations("common")
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
      <AppPageShell
        title={t("title")}
      >
        {/* Search Bar */}
        <div className="app-section-frame px-6 py-6 sm:px-8">
          <div className="flex flex-col gap-3 md:flex-row">
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
        </div>

        {/* Results */}
        <section className="app-section-frame px-4 py-4 sm:px-6 sm:py-6">
          <div className="flex flex-col gap-4">
            {!isLoading && data && (
              <div className="flex justify-end px-2">
                <span className="text-sm text-stone-500">
                  {tc("totalResults", {
                    total: data.total,
                    page: data.page,
                    pages: data.total_pages,
                  })}
                </span>
              </div>
            )}

            {isLoading ? (
              <div className="space-y-4">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Card key={i}>
                    <CardContent className="p-6">
                      <div className="mb-4 flex items-center gap-2">
                        <Skeleton className="h-5 w-12" />
                        <Skeleton className="h-4 w-24" />
                      </div>
                      <Skeleton className="mb-2 h-6 w-3/4" />
                      <Skeleton className="mb-4 h-4 w-full" />
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
              <div className="space-y-4">
                {data?.items.length === 0 && (
                  <AppEmptyState
                    title={t("noResults")}
                    description={t("noResultsHint")}
                    icon={<Search className="h-5 w-5" />}
                  />
                )}
                {data?.items.map((opp) => (
                  <Link
                    key={opp.id}
                    href={`/${locale}/opportunities/${opp.id}`}
                    className="block group"
                  >
                    <Card className="app-card-interactive">
                      <CardContent className="p-6">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <Badge
                                variant={
                                  opp.source === "adb"
                                    ? "default"
                                    : opp.source === "wb"
                                      ? "secondary"
                                      : "outline"
                                }
                                className="uppercase"
                              >
                                {opp.source}
                              </Badge>
                              <span className="text-xs text-muted-foreground">
                                {opp.project_number}
                              </span>
                            </div>
                            <h3 className="mt-3 text-lg font-semibold transition-colors group-hover:text-slate-700">
                              {opp.title}
                            </h3>
                            {opp.description && (
                              <p className="mt-2 line-clamp-2 text-sm leading-7 text-stone-600">
                                {truncate(opp.description, 200)}
                              </p>
                            )}
                            <div className="mt-4 flex flex-wrap gap-4 text-sm text-stone-500">
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
                                  <span>
                                    {formatCurrency(
                                      opp.budget_max,
                                      opp.currency || "USD"
                                    )}
                                  </span>
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
              <div className="flex flex-wrap items-center justify-center gap-1 border-t border-stone-200 px-2 pt-4">
                {/* Prev */}
                <Button
                  variant="outline"
                  size="sm"
                  disabled={params.page <= 1}
                  onClick={() => setParams((p) => ({ ...p, page: p.page - 1 }))}
                >
                  ‹
                </Button>

                {(() => {
                  const current = params.page
                  const total = data.total_pages
                  const pages: (number | "…")[] = []

                  if (total <= 9) {
                    for (let i = 1; i <= total; i++) pages.push(i)
                  } else {
                    pages.push(1)
                    if (current > 4) pages.push("…")
                    for (
                      let i = Math.max(2, current - 2);
                      i <= Math.min(total - 1, current + 2);
                      i++
                    ) {
                      pages.push(i)
                    }
                    if (current < total - 3) pages.push("…")
                    pages.push(total)
                  }

                  return pages.map((p, idx) =>
                    p === "…" ? (
                      <span key={`ellipsis-${idx}`} className="px-1 text-stone-400 select-none">…</span>
                    ) : (
                      <Button
                        key={p}
                        variant={params.page === p ? "default" : "outline"}
                        size="sm"
                        onClick={() => setParams((prev) => ({ ...prev, page: p as number }))}
                      >
                        {p}
                      </Button>
                    )
                  )
                })()}

                {/* Next */}
                <Button
                  variant="outline"
                  size="sm"
                  disabled={params.page >= data.total_pages}
                  onClick={() => setParams((p) => ({ ...p, page: p.page + 1 }))}
                >
                  ›
                </Button>
              </div>
            )}
          </div>
        </section>
      </AppPageShell>
    </MainLayout>
  )
}
