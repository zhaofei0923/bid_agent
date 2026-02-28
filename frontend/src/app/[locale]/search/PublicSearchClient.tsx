"use client"

import { useState } from "react"
import Link from "next/link"
import { useTranslations } from "next-intl"
import OppSearchPanel from "@/components/opportunities/OppSearchPanel"
import OppList from "@/components/opportunities/OppList"
import OppCard from "@/components/opportunities/OppCard"
import { usePublicOpportunities } from "@/hooks/use-opportunities"
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
    const { status, ...rest } = newParams
    setParams(rest)
  }

  const handlePageChange = (newPage: number) => {
    if (newPage > MAX_PUBLIC_PAGE) return
    setParams((prev) => ({ ...prev, page: newPage }))
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">
          {t("title")}
        </h1>
        <p className="mt-3 text-lg text-gray-600">
          {t("subtitle")}
        </p>
      </div>

      {/* Search Panel — hide status filter since we only show open */}
      <div className="mb-6">
        <OppSearchPanel
          params={{ ...params, status: "open" }}
          onSearch={handleSearch}
          hideStatus
        />
      </div>

      {/* Results */}
      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="h-32 animate-pulse rounded-xl border bg-gray-100"
            />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="rounded-xl border bg-white py-16 text-center text-gray-500">
          {t("noResults")}
        </div>
      ) : (
        <div>
          <p className="mb-4 text-sm text-gray-500">
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
            <div className="mt-6 flex items-center justify-center gap-2">
              <button
                onClick={() => handlePageChange(page - 1)}
                disabled={page <= 1}
                className="rounded-lg border px-3 py-1.5 text-sm disabled:opacity-50"
              >
                {tc("prevPage")}
              </button>
              {Array.from({
                length: Math.min(totalPages, MAX_PUBLIC_PAGE),
              }).map((_, i) => {
                const pageNum = i + 1
                return (
                  <button
                    key={pageNum}
                    onClick={() => handlePageChange(pageNum)}
                    className={`rounded-lg px-3 py-1.5 text-sm ${
                      page === pageNum
                        ? "bg-blue-600 text-white"
                        : "border hover:bg-gray-50"
                    }`}
                  >
                    {pageNum}
                  </button>
                )
              })}
              <button
                onClick={() => handlePageChange(page + 1)}
                disabled={page >= Math.min(totalPages, MAX_PUBLIC_PAGE)}
                className="rounded-lg border px-3 py-1.5 text-sm disabled:opacity-50"
              >
                {tc("nextPage")}
              </button>
            </div>
          )}

          {/* Registration CTA when page limit reached */}
          {isAtLimit && (
            <div className="mt-8 rounded-xl border-2 border-dashed border-blue-300 bg-blue-50 p-8 text-center">
              <p className="text-lg font-semibold text-gray-900">
                {t("registerCta")}
              </p>
              <p className="mt-2 text-sm text-gray-600">
                {t("registerCtaDesc")}
              </p>
              <Link
                href={`/${locale}/auth/register`}
                className="mt-4 inline-block rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700 transition"
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
