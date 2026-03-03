"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectOption } from "@/components/ui/select"
import type { OpportunitySearchParams } from "@/types"

const SOURCES = ["all", "adb", "wb"] as const
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
    <div className="app-surface px-6 py-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end">
        {/* Keyword */}
        <div className="flex-1">
          <label className="mb-2 block text-sm font-medium text-stone-700">
            {t("search")}
          </label>
          <Input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder={t("search")}
          />
        </div>

        {/* Source Filter */}
        <div>
          <label className="mb-2 block text-sm font-medium text-stone-700">
            {t("institution")}
          </label>
          <Select
            value={source}
            onValueChange={setSource}
          >
            {SOURCES.map((s) => (
              <SelectOption key={s} value={s}>
                {s === "all" ? tc("all") : s.toUpperCase()}
              </SelectOption>
            ))}
          </Select>
        </div>

        {/* Status Filter */}
        {!hideStatus && (
          <div>
            <label className="mb-2 block text-sm font-medium text-stone-700">
              {t("status")}
            </label>
            <Select
              value={status}
              onValueChange={setStatus}
            >
              {STATUSES.map((s) => (
                <SelectOption key={s} value={s}>
                  {s === "all" ? tc("all") : s === "open" ? t("statusOpen") : t("statusClosed")}
                </SelectOption>
              ))}
            </Select>
          </div>
        )}

        {/* Country */}
        <div>
          <label className="mb-2 block text-sm font-medium text-stone-700">
            {t("country")}
          </label>
          <Input
            type="text"
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            placeholder={t("country")}
            className="w-full md:w-36"
          />
        </div>

        {/* Buttons */}
        <div className="flex gap-2">
          <Button onClick={handleSearch}>
            {t("filters")}
          </Button>
          <Button onClick={handleReset} variant="outline">
            {tc("reset")}
          </Button>
        </div>
      </div>
    </div>
  )
}
