"use client"

import { use } from "react"
import { useTranslations } from "next-intl"
import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { opportunityService } from "@/services/opportunities"
import { formatDate, formatCurrency } from "@/lib/utils"
import { MainLayout } from "@/components/layout/MainLayout"

export default function OpportunityDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const t = useTranslations("opportunities")
  const tc = useTranslations("common")
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"

  const { data: opp, isLoading } = useQuery({
    queryKey: ["opportunity", id],
    queryFn: () => opportunityService.getById(id),
  })

  if (isLoading) return <MainLayout><div className="p-8 text-center">{tc("loading")}</div></MainLayout>
  if (!opp) return <MainLayout><div className="p-8 text-center">{t("notFound")}</div></MainLayout>

  return (
    <MainLayout>
      <main className="container mx-auto px-6 py-8">
        <Link href={`/${locale}/opportunities`} className="text-gray-500 hover:text-gray-700 text-sm">
          {tc("backToList")}
        </Link>

        <div className="mt-4 rounded-xl bg-white p-8 shadow-sm">
          <div className="flex items-center gap-3">
            <span className="rounded bg-blue-100 px-2 py-1 text-sm font-medium text-blue-700 uppercase">
              {opp.source}
            </span>
            <span className={`rounded px-2 py-1 text-sm ${
              opp.status === "open"
                ? "bg-green-100 text-green-700"
                : "bg-gray-100 text-gray-600"
            }`}>
              {opp.status === "open" ? t("statusOpen") : t("statusClosed")}
            </span>
          </div>

          <h1 className="mt-4 text-2xl font-bold">{opp.title}</h1>

          {opp.project_number && (
            <p className="mt-1 text-gray-500">{t("projectNumber")}: {opp.project_number}</p>
          )}

          <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {opp.organization && (
              <div>
                <p className="text-sm text-gray-500">{t("organization")}</p>
                <p className="font-medium">{opp.organization}</p>
              </div>
            )}
            {opp.country && (
              <div>
                <p className="text-sm text-gray-500">{t("country")}</p>
                <p className="font-medium">{opp.country}</p>
              </div>
            )}
            {opp.deadline && (
              <div>
                <p className="text-sm text-gray-500">{t("deadline")}</p>
                <p className="font-medium">{formatDate(opp.deadline)}</p>
              </div>
            )}
            {opp.budget_max && (
              <div>
                <p className="text-sm text-gray-500">{t("budget")}</p>
                <p className="font-medium">
                  {formatCurrency(opp.budget_max, opp.currency || "USD")}
                </p>
              </div>
            )}
          </div>

          {opp.description && (
            <div className="mt-8">
              <h2 className="text-lg font-semibold">{t("description")}</h2>
              <p className="mt-2 whitespace-pre-wrap text-gray-700">
                {opp.description}
              </p>
            </div>
          )}

          <div className="mt-8 flex gap-4">
            <Link
              href={`/${locale}/projects?opportunity_id=${opp.id}`}
              className="rounded-lg bg-blue-600 px-6 py-2 text-white hover:bg-blue-700 transition"
            >
              {t("createProject")}
            </Link>
            {opp.url && (
              <a
                href={opp.url}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-lg border px-6 py-2 hover:bg-gray-50 transition"
              >
                {t("viewOriginal")}
              </a>
            )}
          </div>
        </div>
      </main>
    </MainLayout>
  )
}
