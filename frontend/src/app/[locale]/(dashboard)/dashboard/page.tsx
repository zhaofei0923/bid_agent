"use client"

import { useTranslations } from "next-intl"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { MainLayout } from "@/components/layout/MainLayout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Briefcase, Globe, Coins, Search, PlusCircle, FolderOpen } from "lucide-react"

export default function DashboardPage() {
  const t = useTranslations("dashboard")
  const tc = useTranslations("common")
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"

  return (
    <MainLayout>
      <main className="container mx-auto px-6 py-8">
        <h1 className="text-3xl font-bold tracking-tight">{t("title")}</h1>

        {/* Stats Cards */}
        <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {/* Active Projects */}
          <Card className="hover:shadow-md transition-all duration-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {t("activeProjects")}
              </CardTitle>
              <Briefcase className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">0</div>
            </CardContent>
          </Card>

          {/* Available Opportunities */}
          <Card className="hover:shadow-md transition-all duration-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {t("totalOpportunities")}
              </CardTitle>
              <Globe className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">0</div>
            </CardContent>
          </Card>

          {/* Credits Balance */}
          <Card className="hover:shadow-md transition-all duration-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {t("creditsBalance")}
              </CardTitle>
              <Coins className="h-4 w-4 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">0</div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Start */}
        <section className="mt-12">
          <h2 className="text-xl font-semibold tracking-tight">{t("quickStart")}</h2>
          <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2">
            <Link href={`/${locale}/opportunities`}>
              <Card className="group hover:-translate-y-1 hover:shadow-lg hover:border-blue-200 transition-all duration-200 cursor-pointer h-full">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-blue-100 p-2 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                      <Search className="h-5 w-5 text-blue-600 group-hover:text-white" />
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
              <Card className="group hover:-translate-y-1 hover:shadow-lg hover:border-purple-200 transition-all duration-200 cursor-pointer h-full">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-purple-100 p-2 group-hover:bg-purple-600 group-hover:text-white transition-colors">
                      <PlusCircle className="h-5 w-5 text-purple-600 group-hover:text-white" />
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

        {/* Recent Projects */}
        <section className="mt-12">
          <h2 className="text-xl font-semibold tracking-tight">{t("recentProjects")}</h2>
          <Card className="mt-6 border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12 text-center">
              <div className="rounded-full bg-muted p-3 mb-4">
                <FolderOpen className="h-6 w-6 text-muted-foreground" />
              </div>
              <p className="text-sm text-muted-foreground">{tc("noData")}</p>
            </CardContent>
          </Card>
        </section>
      </main>
    </MainLayout>
  )
}
