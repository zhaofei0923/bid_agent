"use client"

import { useState } from "react"
import { usePathname } from "next/navigation"
import Link from "next/link"
import { useQuery } from "@tanstack/react-query"
import { useTranslations } from "next-intl"
import { MainLayout } from "@/components/layout/MainLayout"
import { AppPageShell } from "@/components/layout/AppPageShell"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { adminService } from "@/services/admin"
import { Search, ChevronLeft, ChevronRight } from "lucide-react"

export default function AdminUsersPage() {
  const t = useTranslations("admin")
  const tc = useTranslations("common")
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"

  const [search, setSearch] = useState("")
  const [inputValue, setInputValue] = useState("")
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ["admin-users", search, page],
    queryFn: () => adminService.listUsers({ search: search || undefined, page, page_size: 20 }),
  })

  const handleSearch = () => {
    setSearch(inputValue)
    setPage(1)
  }

  return (
    <MainLayout>
      <AppPageShell eyebrow={tc("appName")} title={t("title")} description={t("subtitle")}>
        {/* Search */}
        <div className="mb-6 flex gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-stone-400" />
            <Input
              className="pl-9"
              placeholder={t("searchPlaceholder")}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
          </div>
          <Button onClick={handleSearch}>{tc("search")}</Button>
        </div>

        {/* Table */}
        <div className="rounded-xl border border-stone-200 bg-white overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-stone-50 border-b border-stone-100">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-stone-500">{t("colEmail")}</th>
                  <th className="px-4 py-3 text-left font-medium text-stone-500">{t("colName")}</th>
                  <th className="px-4 py-3 text-left font-medium text-stone-500">{t("colCompany")}</th>
                  <th className="px-4 py-3 text-right font-medium text-stone-500">{t("colCredits")}</th>
                  <th className="px-4 py-3 text-left font-medium text-stone-500">{t("colRole")}</th>
                  <th className="px-4 py-3 text-left font-medium text-stone-500">{t("colVerified")}</th>
                  <th className="px-4 py-3 text-left font-medium text-stone-500">{t("colJoined")}</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {isLoading ? (
                  <tr>
                    <td colSpan={8} className="py-12 text-center text-stone-400">
                      {tc("loading")}
                    </td>
                  </tr>
                ) : !data?.items.length ? (
                  <tr>
                    <td colSpan={8} className="py-12 text-center text-stone-400">
                      {tc("noData")}
                    </td>
                  </tr>
                ) : (
                  data.items.map((user) => (
                    <tr key={user.id} className="hover:bg-stone-50/50 transition-colors">
                      <td className="px-4 py-3 font-medium">{user.email}</td>
                      <td className="px-4 py-3">{user.name}</td>
                      <td className="px-4 py-3 text-stone-500">{user.company ?? "—"}</td>
                      <td className="px-4 py-3 text-right font-mono font-semibold">
                        {user.credits_balance}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={user.role === "admin" ? "default" : "secondary"}>
                          {user.role === "admin" ? t("roleAdmin") : t("roleUser")}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={user.is_verified ? "outline" : "destructive"}>
                          {user.is_verified ? t("verified") : t("unverified")}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-stone-400 text-xs whitespace-nowrap">
                        {new Date(user.created_at).toLocaleDateString(
                          locale === "zh" ? "zh-CN" : "en-US"
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <Button asChild variant="ghost" size="sm">
                          <Link href={`/${locale}/admin/users/${user.id}`}>{t("manage")}</Link>
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="mt-4 flex items-center justify-between text-sm text-stone-500">
            <span>
              {tc("totalResults", { total: data.total, page: data.page, pages: data.pages })}
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                <ChevronLeft className="h-4 w-4" />
                {tc("prevPage")}
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= data.pages}
                onClick={() => setPage((p) => p + 1)}
              >
                {tc("nextPage")}
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </AppPageShell>
    </MainLayout>
  )
}
