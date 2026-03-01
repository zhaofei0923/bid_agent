"use client"

import Link from "next/link"
import { useLocale } from "next-intl"
import { formatDate, formatCurrency, truncate } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import type { Opportunity } from "@/types"

interface OppCardProps {
  opportunity: Opportunity
  linkMode?: "internal" | "external"
}

export default function OppCard({ opportunity: opp, linkMode = "internal" }: OppCardProps) {
  const locale = useLocale()

  const statusColors: Record<string, string> = {
    open: "bg-green-100 text-green-700",
    closed: "bg-gray-100 text-gray-600",
    awarded: "bg-blue-100 text-blue-700",
  }

  const href = linkMode === "external" && opp.url ? opp.url : `/${locale}/opportunities/${opp.id}`
  const isExternal = linkMode === "external" && opp.url

  if (isExternal) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="app-surface block px-6 py-6 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_28px_70px_-48px_rgba(15,23,42,0.18)]"
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="secondary">
                {opp.source}
              </Badge>
              {opp.status && (
                <span
                  className={`rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] ${
                    statusColors[opp.status] ?? statusColors.open
                  }`}
                >
                  {opp.status}
                </span>
              )}
              {opp.project_number && (
                <span className="text-xs text-stone-400">{opp.project_number}</span>
              )}
              <span className="ml-auto text-xs text-stone-400">↗</span>
            </div>

            <h3 className="mt-3 text-xl font-semibold tracking-[-0.02em] text-slate-900">
              {opp.title}
            </h3>

            {opp.description && (
              <p className="mt-2 text-sm leading-7 text-stone-600">
                {truncate(opp.description, 200)}
              </p>
            )}

            <div className="mt-4 flex flex-wrap gap-4 text-sm text-stone-500">
              {opp.country && <span>📍 {opp.country}</span>}
              {opp.sector && <span>📂 {opp.sector}</span>}
              {opp.deadline && <span>⏰ {formatDate(opp.deadline)}</span>}
              {opp.budget_max && (
                <span>
                  💰 {formatCurrency(opp.budget_max, opp.currency ?? "USD")}
                </span>
              )}
            </div>
          </div>
        </div>
      </a>
    )
  }

  return (
    <Link
      href={href}
      className="app-surface block px-6 py-6 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_28px_70px_-48px_rgba(15,23,42,0.18)]"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">
              {opp.source}
            </Badge>
            {opp.status && (
              <span
                className={`rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] ${
                  statusColors[opp.status] ?? statusColors.open
                }`}
              >
                {opp.status}
              </span>
            )}
            {opp.project_number && (
              <span className="text-xs text-stone-400">{opp.project_number}</span>
            )}
          </div>

          <h3 className="mt-3 text-xl font-semibold tracking-[-0.02em] text-slate-900">
            {opp.title}
          </h3>

          {opp.description && (
            <p className="mt-2 text-sm leading-7 text-stone-600">
              {truncate(opp.description, 200)}
            </p>
          )}

          <div className="mt-4 flex flex-wrap gap-4 text-sm text-stone-500">
            {opp.country && <span>📍 {opp.country}</span>}
            {opp.sector && <span>📂 {opp.sector}</span>}
            {opp.deadline && <span>⏰ {formatDate(opp.deadline)}</span>}
            {opp.budget_max && (
              <span>
                💰 {formatCurrency(opp.budget_max, opp.currency ?? "USD")}
              </span>
            )}
          </div>
        </div>
      </div>
    </Link>
  )
}
