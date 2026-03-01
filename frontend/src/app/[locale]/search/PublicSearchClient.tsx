"use client"

import { useState } from "react"
import Link from "next/link"
import { useTranslations } from "next-intl"
import OppSearchPanel from "@/components/opportunities/OppSearchPanel"
import OppCard from "@/components/opportunities/OppCard"
import { usePublicOpportunities } from "@/hooks/use-opportunities"
import { Button } from "@/components/ui/button"
import { AppEmptyState } from "@/components/layout/AppEmptyState"
import type { OpportunitySearchParams } from "@/types"

const MAX_PUBLIC_PAGE = 5

interface PublicSearchClientProps {
  locale: string
}

export default function PublicSearchClient({ locale }: PublicSearchClientProps) {
  const t = useTranslations("publicSearch")
  const tc = useTranslations("common")
  const [params, setParams] = useState<Omit<OpportunitySearchParams, "status">>({
    page: 1,
    page_size: 20,
  })

  const { data, isLoading } = usePublicOpportunities(params)

  const items = data?.items ?? []
  const total = data?.total ?? 0
  const page = data?.page ?? 1
  const pageSize = data?.page_size ?? 20
  const totalPages = Math.ceil(total / pageSize)
  const isAtLimit = page >= MAX_PUBLIC_PAGE && totalPages > MAX_PUBLIC_PAGE

  const handleSearch = (newParams: OpportunitySearchParams) => {
    // Strip status since public endpoint forces open
    const rest = { ...newParams }
    delete rest.status
    setParams(rest)
  }

  const handlePageChange = (newPage: number) => {
    if (newPage > MAX_PUBLIC_PAGE) return
    setParams((prev) => ({ ...prev, page: newPage }))
  }

  return (
    <div className="pb-8">
      <section className="app-panel px-6 py-10 text-center sm:px-8">
        <p className="app-page-kicker">{t("title")}</p>
        <h1 className="landing-v2-display mt-4 text-4xl font-semibold text-slate-900 md:text-5xl">
          {t("title")}
        </h1>
        <p className="mx-auto mt-4 max-w-3xl text-base leading-8 text-stone-600 sm:text-lg">
          {t("subtitle")}
        </p>
      </section>

      {/* Search Panel — hide status filter since we only show open */}
      <div className="mt-8">
        <OppSearchPanel
          params={{ ...params, status: "open" }}
          onSearch={handleSearch}
          hideStatus
        />
      </div>

      {/* Results */}
      {isLoading ? (
        <div className="mt-6 space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="app-surface h-32 animate-pulse"
            />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="mt-6">
          <AppEmptyState title={t("noResults")} description={t("registerCtaDesc")} />
        </div>
      ) : (
        <div className="mt-6">
          <p className="mb-4 text-sm text-stone-500">
            {tc("totalResults", {
              total,
              page,
              pages: Math.min(totalPages, MAX_PUBLIC_PAGE),
            })}
          </p>

          <div className="space-y-4">
            {items.map((opp) => (
              <OppCard key={opp.id} opportunity={opp} linkMode="external" />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-8 flex flex-wrap items-center justify-center gap-2">
              <Button
                onClick={() => handlePageChange(page - 1)}
                disabled={page <= 1}
                variant="outline"
                size="sm"
              >
                {tc("prevPage")}
              </Button>
              {Array.from({
                length: Math.min(totalPages, MAX_PUBLIC_PAGE),
              }).map((_, i) => {
                const pageNum = i + 1
                return (
                  <Button
                    key={pageNum}
                    onClick={() => handlePageChange(pageNum)}
                    variant={page === pageNum ? "default" : "outline"}
                    size="sm"
                  >
                    {pageNum}
                  </Button>
                )
              })}
              <Button
                onClick={() => handlePageChange(page + 1)}
                disabled={page >= Math.min(totalPages, MAX_PUBLIC_PAGE)}
                variant="outline"
                size="sm"
              >
                {tc("nextPage")}
              </Button>
            </div>
          )}

          {/* Registration CTA when page limit reached */}
          {isAtLimit && (
            <div className="app-surface-muted mt-10 px-6 py-8 text-center sm:px-8">
              <p className="landing-v2-display text-2xl font-semibold text-slate-900">
                {t("registerCta")}
              </p>
              <p className="mx-auto mt-3 max-w-2xl text-sm leading-7 text-stone-600">
                {t("registerCtaDesc")}
              </p>
              <Link
                href={`/${locale}/auth/register`}
                className="mt-5 inline-flex h-11 items-center rounded-full bg-slate-900 px-6 text-sm font-semibold text-white transition-colors duration-200 hover:bg-slate-800"
              >
                {t("registerBtn")}
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
