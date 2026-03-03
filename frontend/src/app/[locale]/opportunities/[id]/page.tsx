"use client"

import { use } from "react"
import { useTranslations } from "next-intl"
import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { opportunityService } from "@/services/opportunities"
import { formatDate, formatCurrency } from "@/lib/utils"
import { MainLayout } from "@/components/layout/MainLayout"
import { AppPageShell } from "@/components/layout/AppPageShell"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

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
      <AppPageShell
        eyebrow={t("projectNumber")}
        title={opp.title}
        description={opp.description || undefined}
        actions={
          <>
            <Button asChild variant="outline">
              <Link href={`/${locale}/opportunities`}>{tc("backToList")}</Link>
            </Button>
            <Button asChild>
              <Link href={`/${locale}/projects?opportunity_id=${opp.id}`}>
                {t("createProject")}
              </Link>
            </Button>
          </>
        }
      >
        <div className="app-section-frame px-6 py-8 sm:px-8">
          <div className="flex flex-wrap items-center gap-3">
            <Badge variant="secondary">
              {opp.source}
            </Badge>
            <span className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] ${
              opp.status === "open"
                ? "bg-emerald-100 text-emerald-700"
                : "bg-stone-100 text-stone-600"
            }`}>
              {opp.status === "open" ? t("statusOpen") : t("statusClosed")}
            </span>
            {opp.project_number && (
              <span className="text-xs font-medium uppercase tracking-[0.12em] text-stone-400">
                {opp.project_number}
              </span>
            )}
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {opp.organization && (
              <div className="app-surface-muted px-4 py-4">
                <p className="app-detail-label">{t("organization")}</p>
                <p className="app-detail-value mt-2">{opp.organization}</p>
              </div>
            )}
            {opp.country && (
              <div className="app-surface-muted px-4 py-4">
                <p className="app-detail-label">{t("country")}</p>
                <p className="app-detail-value mt-2">{opp.country}</p>
              </div>
            )}
            {opp.deadline && (
              <div className="app-surface-muted px-4 py-4">
                <p className="app-detail-label">{t("deadline")}</p>
                <p className="app-detail-value mt-2">{formatDate(opp.deadline)}</p>
              </div>
            )}
            {opp.budget_max && (
              <div className="app-surface-muted px-4 py-4">
                <p className="app-detail-label">{t("budget")}</p>
                <p className="app-detail-value mt-2">
                  {formatCurrency(opp.budget_max, opp.currency || "USD")}
                </p>
              </div>
            )}
          </div>

          {opp.description && (
            <div className="mt-8">
              <h2 className="app-section-title">{t("description")}</h2>
              <p className="mt-4 whitespace-pre-wrap text-sm leading-8 text-stone-600">
                {opp.description}
              </p>
            </div>
          )}

          <div className="mt-8 flex flex-wrap gap-3">
            {opp.url && (
              <Button asChild variant="outline">
                <a href={opp.url} target="_blank" rel="noopener noreferrer">
                  {t("viewOriginal")}
                </a>
              </Button>
            )}
          </div>
        </div>
      </AppPageShell>
    </MainLayout>
  )
}
