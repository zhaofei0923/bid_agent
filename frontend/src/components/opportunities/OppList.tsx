"use client"

import { useTranslations } from "next-intl"
import type { Opportunity } from "@/types"
import OppCard from "./OppCard"

interface OppListProps {
  items: Opportunity[]
  total: number
  page: number
  pageSize: number
  onPageChange: (page: number) => void
  isLoading?: boolean
}

export default function OppList({
  items,
  total,
  page,
  pageSize,
  onPageChange,
  isLoading,
}: OppListProps) {
  const t = useTranslations("opportunities")
  const tc = useTranslations("common")
  const totalPages = Math.ceil(total / pageSize)

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div
            key={i}
            className="h-32 animate-pulse rounded-xl border bg-gray-100"
          />
        ))}
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="rounded-xl border bg-white py-16 text-center text-gray-500">
        {t("noResultsHint")}
      </div>
    )
  }

  return (
    <div>
      <p className="mb-4 text-sm text-gray-500">
        {tc("totalResults", { total, page, pages: totalPages })}
      </p>

      <div className="space-y-4">
        {items.map((opp) => (
          <OppCard key={opp.id} opportunity={opp} />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-6 flex items-center justify-center gap-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="rounded-lg border px-3 py-1.5 text-sm disabled:opacity-50"
          >
            {tc("prevPage")}
          </button>
          {Array.from({ length: Math.min(totalPages, 7) }).map((_, i) => {
            const pageNum = i + 1
            return (
              <button
                key={pageNum}
                onClick={() => onPageChange(pageNum)}
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
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="rounded-lg border px-3 py-1.5 text-sm disabled:opacity-50"
          >
            {tc("nextPage")}
          </button>
        </div>
      )}
    </div>
  )
}
