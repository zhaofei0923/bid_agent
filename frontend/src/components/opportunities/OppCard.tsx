"use client"

import Link from "next/link"
import { useLocale } from "next-intl"
import { formatDate, formatCurrency, truncate } from "@/lib/utils"
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
        className="block rounded-xl border bg-white p-6 hover:shadow-md transition"
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700 uppercase">
                {opp.source}
              </span>
              {opp.status && (
                <span
                  className={`rounded px-2 py-0.5 text-xs font-medium ${
                    statusColors[opp.status] ?? statusColors.open
                  }`}
                >
                  {opp.status}
                </span>
              )}
              {opp.project_number && (
                <span className="text-xs text-gray-400">{opp.project_number}</span>
              )}
              <span className="ml-auto text-xs text-blue-500">↗</span>
            </div>

            <h3 className="mt-2 text-lg font-semibold text-gray-900">
              {opp.title}
            </h3>

            {opp.description && (
              <p className="mt-1 text-sm text-gray-600">
                {truncate(opp.description, 200)}
              </p>
            )}

            <div className="mt-3 flex flex-wrap gap-4 text-sm text-gray-500">
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
      className="block rounded-xl border bg-white p-6 hover:shadow-md transition"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700 uppercase">
              {opp.source}
            </span>
            {opp.status && (
              <span
                className={`rounded px-2 py-0.5 text-xs font-medium ${
                  statusColors[opp.status] ?? statusColors.open
                }`}
              >
                {opp.status}
              </span>
            )}
            {opp.project_number && (
              <span className="text-xs text-gray-400">{opp.project_number}</span>
            )}
          </div>

          <h3 className="mt-2 text-lg font-semibold text-gray-900">
            {opp.title}
          </h3>

          {opp.description && (
            <p className="mt-1 text-sm text-gray-600">
              {truncate(opp.description, 200)}
            </p>
          )}

          <div className="mt-3 flex flex-wrap gap-4 text-sm text-gray-500">
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
