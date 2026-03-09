"use client"

import { useTranslations } from "next-intl"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { MainLayout } from "@/components/layout/MainLayout"
import { AppPageShell } from "@/components/layout/AppPageShell"
import { AppEmptyState } from "@/components/layout/AppEmptyState"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { LatestOpportunities } from "@/components/opportunities/LatestOpportunities"
import { useProjects } from "@/hooks/use-projects"
import { useOpportunities } from "@/hooks/use-opportunities"
import { useCreditsBalance } from "@/hooks/use-credits"
import { Briefcase, Globe, Coins, Search, PlusCircle, FolderOpen, ArrowRight } from "lucide-react"
import { formatRelative } from "@/lib/utils"
import type { ProjectStatus } from "@/types/project"

const STATUS_LABEL: Record<ProjectStatus, string> = {
  draft: "草稿",
  created: "进行中",
  analyzing: "分析中",
  analyzed: "已分析",
  guiding: "指导中",
  completed: "已完成",
  archived: "已归档",
}

const STATUS_VARIANT: Record<ProjectStatus, "secondary" | "outline" | "default" | "destructive"> = {
  draft: "outline",
  created: "secondary",
  analyzing: "secondary",
  analyzed: "default",
  guiding: "default",
  completed: "default",
  archived: "outline",
}

export default function DashboardPage() {
  const t = useTranslations("dashboard")
  const tc = useTranslations("common")
  const topp = useTranslations("opportunities")
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"

  const { data: projectsData, isLoading: projectsLoading } = useProjects({ page: 1, page_size: 3 })
  const { data: opportunitiesData, isLoading: oppsLoading } = useOpportunities({ page: 1, page_size: 1 })
  const { data: creditsBalance, isLoading: creditsLoading } = useCreditsBalance()

  const activeProjectsCount = projectsLoading ? null : (projectsData?.total ?? 0)
  const opportunitiesCount = oppsLoading ? null : (opportunitiesData?.total ?? 0)
  const credits = creditsLoading ? null : (creditsBalance ?? 0)

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
          <Link href={`/${locale}/projects`}>
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
                <div className="app-metric-value">
                  {activeProjectsCount === null ? "—" : activeProjectsCount}
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Available Opportunities */}
          <Link href={`/${locale}/opportunities`}>
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
                <div className="app-metric-value">
                  {opportunitiesCount === null ? "—" : opportunitiesCount}
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Credits Balance */}
          <Link href={`/${locale}/credits`}>
            <Card className="app-card-interactive app-stat-card h-full">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-stone-500">
                  {t("creditsBalance")}
                </CardTitle>
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-amber-50 text-amber-700">
                  <Coins className="h-4 w-4" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="app-metric-value">
                  {credits === null ? "—" : credits}
                </div>
              </CardContent>
            </Card>
          </Link>
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
          <div className="flex items-center justify-between">
            <div>
              <p className="app-page-kicker">{t("recentProjects")}</p>
              <h2 className="app-section-title mt-3">{t("recentProjects")}</h2>
            </div>
            <Link
              href={`/${locale}/projects`}
              className="flex items-center gap-1 text-sm text-stone-500 transition-colors hover:text-slate-900"
            >
              {topp("viewAll")} <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
          <div className="mt-6">
            {projectsLoading ? (
              <div className="py-8 text-center text-sm text-stone-400">{tc("loading")}</div>
            ) : projectsData && projectsData.items.length > 0 ? (
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {projectsData.items.map((project) => (
                  <Link key={project.id} href={`/${locale}/projects/${project.id}`}>
                    <Card className="app-card-interactive h-full">
                      <CardHeader>
                        <div className="flex items-start justify-between gap-4">
                          <CardTitle className="text-base">{project.name}</CardTitle>
                          <Badge variant={STATUS_VARIANT[project.status as ProjectStatus] ?? "secondary"}>
                            {STATUS_LABEL[project.status as ProjectStatus] ?? project.status}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        {project.description && (
                          <p className="line-clamp-2 text-sm leading-6 text-stone-500">
                            {project.description}
                          </p>
                        )}
                        <div className="mt-4 flex items-center justify-between text-xs text-stone-400">
                          <span>{t("progress")} {project.progress}%</span>
                          <span>{formatRelative(project.created_at)}</span>
                        </div>
                        <div className="app-progress-track mt-2">
                          <div
                            className="app-progress-fill"
                            style={{ width: `${project.progress}%` }}
                          />
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                ))}
              </div>
            ) : (
              <AppEmptyState
                title={tc("noData")}
                icon={<FolderOpen className="h-5 w-5" />}
              />
            )}
          </div>
        </section>
      </AppPageShell>
    </MainLayout>
  )
}
