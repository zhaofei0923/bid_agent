"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import type { OpportunitySearchParams } from "@/types"

const SOURCES = ["all", "adb", "wb", "ungm"] as const
const STATUSES = ["all", "open", "closed"] as const

interface OppSearchPanelProps {
  params: OpportunitySearchParams
  onSearch: (params: OpportunitySearchParams) => void
  hideStatus?: boolean
}

export default function OppSearchPanel({ params, onSearch, hideStatus }: OppSearchPanelProps) {
  const t = useTranslations("opportunities")
  const tc = useTranslations("common")
  const [keyword, setKeyword] = useState(params.search ?? "")
  const [source, setSource] = useState(params.source ?? "all")
  const [status, setStatus] = useState(params.status ?? "all")
  const [country, setCountry] = useState(params.country ?? "")

  const handleSearch = () => {
    onSearch({
      ...params,
      search: keyword || undefined,
      source: source === "all" ? undefined : source,
      status: status === "all" ? undefined : status,
      country: country || undefined,
      page: 1,
    })
  }

  const handleReset = () => {
    setKeyword("")
    setSource("all")
    setStatus("all")
    setCountry("")
    onSearch({ page: 1, page_size: params.page_size ?? 20 })
  }

  return (
    <div className="rounded-xl border bg-white p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end">
        {/* Keyword */}
        <div className="flex-1">
          <label className="mb-1 block text-sm font-medium text-gray-700">
            {t("search")}
          </label>
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder={t("search")}
            className="w-full rounded-lg border px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {/* Source Filter */}
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            {t("institution")}
          </label>
          <select
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="rounded-lg border bg-white px-3 py-2 text-sm"
          >
            {SOURCES.map((s) => (
              <option key={s} value={s}>
                {s === "all" ? tc("all") : s.toUpperCase()}
              </option>
            ))}
          </select>
        </div>

        {/* Status Filter */}
        {!hideStatus && (
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              {t("status")}
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="rounded-lg border bg-white px-3 py-2 text-sm"
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s === "all" ? tc("all") : s === "open" ? t("statusOpen") : t("statusClosed")}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Country */}
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            {t("country")}
          </label>
          <input
            type="text"
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            placeholder="e.g. China"
            className="w-28 rounded-lg border px-3 py-2 text-sm"
          />
        </div>

        {/* Buttons */}
        <div className="flex gap-2">
          <button
            onClick={handleSearch}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 transition"
          >
            {t("filters")}
          </button>
          <button
            onClick={handleReset}
            className="rounded-lg border px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 transition"
          >
            {tc("reset")}
          </button>
        </div>
      </div>
    </div>
  )
}
