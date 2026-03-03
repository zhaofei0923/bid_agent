"use client"

import { useTranslations } from "next-intl"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { MainLayout } from "@/components/layout/MainLayout"
import { AppPageShell } from "@/components/layout/AppPageShell"
import { AppEmptyState } from "@/components/layout/AppEmptyState"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { LatestOpportunities } from "@/components/opportunities/LatestOpportunities"
import { Briefcase, Globe, Coins, Search, PlusCircle, FolderOpen } from "lucide-react"

export default function DashboardPage() {
  const t = useTranslations("dashboard")
  const tc = useTranslations("common")
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"

  return (
    <MainLayout>
      <AppPageShell
        eyebrow={tc("appName")}
        title={t("title")}
        description={t("browseOpportunitiesDesc")}
        actions={
          <>
            <Button asChild variant="outline">
              <Link href={`/${locale}/opportunities`}>{t("browseOpportunities")}</Link>
            </Button>
            <Button asChild>
              <Link href={`/${locale}/projects`}>{t("createProject")}</Link>
            </Button>
          </>
        }
      >

        {/* Stats Cards */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {/* Active Projects */}
          <Card className="app-card-interactive app-stat-card h-full">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-stone-500">
                {t("activeProjects")}
              </CardTitle>
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-stone-100 text-stone-700">
                <Briefcase className="h-4 w-4" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="app-metric-value">0</div>
            </CardContent>
          </Card>

          {/* Available Opportunities */}
          <Card className="app-card-interactive app-stat-card h-full">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-stone-500">
                {t("totalOpportunities")}
              </CardTitle>
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-stone-100 text-stone-700">
                <Globe className="h-4 w-4" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="app-metric-value">0</div>
            </CardContent>
          </Card>

          {/* Credits Balance */}
          <Card className="app-card-interactive app-stat-card h-full">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-stone-500">
                {t("creditsBalance")}
              </CardTitle>
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-stone-100 text-stone-700">
                <Coins className="h-4 w-4" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="app-metric-value">0</div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Start */}
        <section className="app-section-frame px-6 py-6 sm:px-8 sm:py-8">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="app-page-kicker">{t("quickStart")}</p>
              <h2 className="app-section-title mt-3">{t("quickStart")}</h2>
            </div>
          </div>
          <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2">
            <Link href={`/${locale}/opportunities`}>
              <Card className="app-card-interactive group h-full cursor-pointer">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-stone-100 text-stone-700 transition-colors duration-200 group-hover:bg-slate-900 group-hover:text-white">
                      <Search className="h-5 w-5" />
                    </div>
                    <CardTitle className="text-lg">{t("browseOpportunities")}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    {t("browseOpportunitiesDesc")}
                  </p>
                </CardContent>
              </Card>
            </Link>

            <Link href={`/${locale}/projects`}>
              <Card className="app-card-interactive group h-full cursor-pointer">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-stone-100 text-stone-700 transition-colors duration-200 group-hover:bg-slate-900 group-hover:text-white">
                      <PlusCircle className="h-5 w-5" />
                    </div>
                    <CardTitle className="text-lg">{t("startBidProject")}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    {t("createProject")}
                  </p>
                </CardContent>
              </Card>
            </Link>
          </div>
        </section>

        {/* Latest Opportunities */}
        <section className="app-section-frame px-6 py-6 sm:px-8 sm:py-8">
          <p className="app-page-kicker">{t("latestOpportunities")}</p>
          <h2 className="app-section-title mt-3">{t("latestOpportunities")}</h2>
          <div className="mt-6">
            <LatestOpportunities
              locale={locale}
              limit={6}
              linkMode="external"
              showViewAll
            />
          </div>
        </section>

        {/* Recent Projects */}
        <section className="app-section-frame px-6 py-6 sm:px-8 sm:py-8">
          <p className="app-page-kicker">{t("recentProjects")}</p>
          <h2 className="app-section-title mt-3">{t("recentProjects")}</h2>
          <div className="mt-6">
            <AppEmptyState
              title={tc("noData")}
              icon={<FolderOpen className="h-5 w-5" />}
            />
          </div>
        </section>
      </AppPageShell>
    </MainLayout>
  )
}
