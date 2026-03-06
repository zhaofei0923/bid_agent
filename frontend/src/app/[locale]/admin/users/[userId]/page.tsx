"use client"

import { useState } from "react"
import { usePathname, useParams } from "next/navigation"
import Link from "next/link"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useTranslations } from "next-intl"
import { MainLayout } from "@/components/layout/MainLayout"
import { AppPageShell } from "@/components/layout/AppPageShell"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Select, SelectOption } from "@/components/ui/select"
import { adminService } from "@/services/admin"
import { Coins, User as UserIcon, ArrowUpDown } from "lucide-react"

export default function AdminUserDetailPage() {
  const t = useTranslations("admin")
  const tc = useTranslations("common")
  const params = useParams<{ userId: string }>()
  const pathname = usePathname()
  const locale = pathname.split("/")[1] || "zh"
  const userId = params.userId

  const queryClient = useQueryClient()

  const [dialogOpen, setDialogOpen] = useState(false)
  const [adjustAmount, setAdjustAmount] = useState("")
  const [adjustReason, setAdjustReason] = useState("")
  const [adjustError, setAdjustError] = useState("")

  const [roleDialogOpen, setRoleDialogOpen] = useState(false)
  const [selectedRole, setSelectedRole] = useState<"user" | "admin">("user")

  const { data: user, isLoading: userLoading } = useQuery({
    queryKey: ["admin-user", userId],
    queryFn: () => adminService.getUser(userId),
  })

  const { data: transactions, isLoading: txnLoading } = useQuery({
    queryKey: ["admin-user-txns", userId],
    queryFn: () => adminService.getUserTransactions(userId),
  })

  const adjustMutation = useMutation({
    mutationFn: (vars: { amount: number; reason: string }) =>
      adminService.adjustCredits(userId, vars.amount, vars.reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-user", userId] })
      queryClient.invalidateQueries({ queryKey: ["admin-user-txns", userId] })
      queryClient.invalidateQueries({ queryKey: ["admin-users"] })
      setDialogOpen(false)
      setAdjustAmount("")
      setAdjustReason("")
      setAdjustError("")
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setAdjustError(msg ?? tc("error"))
    },
  })

  const roleMutation = useMutation({
    mutationFn: (role: "user" | "admin") => adminService.updateUserRole(userId, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-user", userId] })
      queryClient.invalidateQueries({ queryKey: ["admin-users"] })
      setRoleDialogOpen(false)
    },
  })

  const handleAdjustSubmit = () => {
    const amount = parseInt(adjustAmount, 10)
    if (isNaN(amount) || amount === 0) {
      setAdjustError(t("adjustAmountError"))
      return
    }
    if (!adjustReason.trim()) {
      setAdjustError(t("adjustReasonRequired"))
      return
    }
    setAdjustError("")
    adjustMutation.mutate({ amount, reason: adjustReason.trim() })
  }

  if (userLoading) {
    return (
      <MainLayout>
        <AppPageShell title="">
          <p className="text-stone-400">{tc("loading")}</p>
        </AppPageShell>
      </MainLayout>
    )
  }

  if (!user) {
    return (
      <MainLayout>
        <AppPageShell title="">
          <p className="text-stone-400">{tc("noData")}</p>
        </AppPageShell>
      </MainLayout>
    )
  }

  return (
    <MainLayout>
      <div className="app-page-wrap">
        <div className="app-panel px-6 py-8 sm:px-8 sm:py-10">
          <Link href={`/${locale}/admin`} className="mb-4 inline-block text-sm text-stone-400 hover:text-stone-700">
            ← {t("title")}
          </Link>
          <AppPageShell title={user.name} description={user.email}>
        <div className="grid gap-6 lg:grid-cols-2">
          {/* User Info Card */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <UserIcon className="h-4 w-4 text-stone-400" />
                <CardTitle className="text-base">{t("userInfo")}</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <InfoRow label={t("colEmail")} value={user.email} />
              <InfoRow label={t("colName")} value={user.name} />
              <InfoRow label={t("colCompany")} value={user.company ?? "—"} />
              <InfoRow
                label={t("colVerified")}
                value={
                  <Badge variant={user.is_verified ? "outline" : "destructive"}>
                    {user.is_verified ? t("verified") : t("unverified")}
                  </Badge>
                }
              />
              <InfoRow
                label={t("colRole")}
                value={
                  <div className="flex items-center gap-2">
                    <Badge variant={user.role === "admin" ? "default" : "secondary"}>
                      {user.role === "admin" ? t("roleAdmin") : t("roleUser")}
                    </Badge>
                    <button
                      type="button"
                      className="text-xs text-stone-400 hover:text-slate-700 underline underline-offset-2"
                      onClick={() => {
                        setSelectedRole(user.role as "user" | "admin")
                        setRoleDialogOpen(true)
                      }}
                    >
                      {t("changeRole")}
                    </button>
                  </div>
                }
              />
              <InfoRow
                label={t("colJoined")}
                value={new Date(user.created_at).toLocaleDateString(
                  locale === "zh" ? "zh-CN" : "en-US"
                )}
              />
            </CardContent>
          </Card>

          {/* Credits Card */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Coins className="h-4 w-4 text-stone-400" />
                  <CardTitle className="text-base">{t("creditsTitle")}</CardTitle>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setDialogOpen(true)}
                >
                  <ArrowUpDown className="mr-1 h-3 w-3" />
                  {t("adjustCredits")}
                </Button>
              </div>
              <CardDescription>
                {t("currentBalance")}:{" "}
                <span className="font-semibold text-slate-900">{user.credits_balance}</span>{" "}
                {tc("credits")}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {txnLoading ? (
                <p className="text-sm text-stone-400">{tc("loading")}</p>
              ) : !transactions?.length ? (
                <p className="text-sm text-stone-400">{t("noTransactions")}</p>
              ) : (
                <div className="rounded-lg border border-stone-100 overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead className="bg-stone-50 border-b border-stone-100">
                        <tr>
                          <th className="px-3 py-2 text-left font-medium text-stone-500">{t("txnType")}</th>
                          <th className="px-3 py-2 text-right font-medium text-stone-500">{t("txnAmount")}</th>
                          <th className="px-3 py-2 text-right font-medium text-stone-500">{t("txnBalance")}</th>
                          <th className="px-3 py-2 text-left font-medium text-stone-500">{t("txnDesc")}</th>
                          <th className="px-3 py-2 text-left font-medium text-stone-500">{t("txnTime")}</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-stone-100">
                        {transactions.map((txn) => (
                          <tr key={txn.id} className="hover:bg-stone-50/50">
                            <td className="px-3 py-2">
                              <Badge
                                variant={txn.amount > 0 ? "outline" : "secondary"}
                                className="text-[10px]"
                              >
                                {txn.type}
                              </Badge>
                            </td>
                            <td
                              className={`px-3 py-2 text-right font-mono font-semibold ${
                                txn.amount > 0 ? "text-green-600" : "text-red-500"
                              }`}
                            >
                              {txn.amount > 0 ? "+" : ""}
                              {txn.amount}
                            </td>
                            <td className="px-3 py-2 text-right font-mono text-stone-500">
                              {txn.balance_after}
                            </td>
                            <td className="px-3 py-2 max-w-[140px] truncate text-stone-500">
                              {txn.description ?? "—"}
                            </td>
                            <td className="px-3 py-2 text-stone-400 whitespace-nowrap">
                              {new Date(txn.created_at).toLocaleDateString(
                                locale === "zh" ? "zh-CN" : "en-US"
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Credit Adjust Dialog */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t("adjustCreditsTitle")}</DialogTitle>
              <DialogDescription>{t("adjustCreditsDesc")}</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div className="space-y-1.5">
                <Label>{t("adjustAmountLabel")}</Label>
                <Input
                  type="number"
                  placeholder={t("adjustAmountPlaceholder")}
                  value={adjustAmount}
                  onChange={(e) => setAdjustAmount(e.target.value)}
                />
                <p className="text-xs text-stone-400">{t("adjustAmountHint")}</p>
              </div>
              <div className="space-y-1.5">
                <Label>{t("adjustReasonLabel")}</Label>
                <Input
                  placeholder={t("adjustReasonPlaceholder")}
                  value={adjustReason}
                  onChange={(e) => setAdjustReason(e.target.value)}
                />
              </div>
              {adjustError && (
                <p className="text-sm text-red-500">{adjustError}</p>
              )}
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setDialogOpen(false)
                  setAdjustError("")
                }}
              >
                {tc("cancel")}
              </Button>
              <Button onClick={handleAdjustSubmit} disabled={adjustMutation.isPending}>
                {adjustMutation.isPending ? tc("processing") : tc("confirm")}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Role Change Dialog */}
        <Dialog open={roleDialogOpen} onOpenChange={setRoleDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t("changeRoleTitle")}</DialogTitle>
              <DialogDescription>{t("changeRoleDesc")}</DialogDescription>
            </DialogHeader>
            <div className="py-2">
              <Select
                value={selectedRole}
                onValueChange={(v) => setSelectedRole(v as "user" | "admin")}
              >
                <SelectOption value="user">{t("roleUser")}</SelectOption>
                <SelectOption value="admin">{t("roleAdmin")}</SelectOption>
              </Select>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setRoleDialogOpen(false)}>
                {tc("cancel")}
              </Button>
              <Button
                onClick={() => roleMutation.mutate(selectedRole)}
                disabled={roleMutation.isPending}
              >
                {roleMutation.isPending ? tc("processing") : tc("confirm")}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
          </AppPageShell>
        </div>
      </div>
    </MainLayout>
  )
}

function InfoRow({
  label,
  value,
}: {
  label: string
  value: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-stone-500 shrink-0">{label}</span>
      <span className="text-right text-slate-900">{value}</span>
    </div>
  )
}
