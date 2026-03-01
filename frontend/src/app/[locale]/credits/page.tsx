"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { useQuery } from "@tanstack/react-query"
import { creditsService } from "@/services/credits"
import { useAuthStore } from "@/stores/auth"
import PaymentDialog from "@/components/payment/PaymentDialog"
import { MainLayout } from "@/components/layout/MainLayout"
import { AppPageShell } from "@/components/layout/AppPageShell"
import { AppEmptyState } from "@/components/layout/AppEmptyState"
import { Button } from "@/components/ui/button"
import { CreditCard } from "lucide-react"

export default function CreditsPage() {
  const t = useTranslations("credits")
  const user = useAuthStore((s) => s.user)
  const [showPayment, setShowPayment] = useState(false)

  const { data: balance } = useQuery({
    queryKey: ["credits", "balance"],
    queryFn: () => creditsService.getBalance(),
  })

  const { data: transactions } = useQuery({
    queryKey: ["credits", "transactions"],
    queryFn: () => creditsService.listTransactions(),
  })

  const { data: packages } = useQuery({
    queryKey: ["credits", "packages"],
    queryFn: () => creditsService.listPackages(),
  })

  return (
    <MainLayout>
      <AppPageShell
        eyebrow={t("creditsUnit")}
        title={t("title")}
        actions={<Button onClick={() => setShowPayment(true)}>{t("recharge")}</Button>}
      >

        {/* Balance Card */}
        <div className="app-panel px-6 py-8 text-slate-900 sm:px-8">
          <p className="app-page-kicker">{t("balance")}</p>
          <p className="landing-v2-display mt-4 text-5xl font-semibold">
            {balance ?? user?.credits_balance ?? 0}
          </p>
          <p className="mt-2 text-sm font-medium text-stone-600">{t("creditsUnit")}</p>
        </div>

        {/* Packages */}
        <div>
          <h2 className="app-section-title">{t("packages")}</h2>
          <div className="mt-4 grid gap-4 md:grid-cols-3">
            {(packages ?? []).map((pkg: { id: string; name: string; credits: number; price: number }) => (
              <div
                key={pkg.id}
                className="app-surface cursor-pointer px-6 py-6 transition-all duration-200 hover:-translate-y-0.5"
                onClick={() => setShowPayment(true)}
              >
                <h3 className="text-lg font-semibold text-slate-900">{pkg.name}</h3>
                <p className="landing-v2-display mt-3 text-4xl font-semibold text-slate-900">
                  {pkg.credits}
                </p>
                <p className="text-sm text-stone-500">{t("creditsUnit")}</p>
                <p className="mt-4 text-lg font-semibold text-stone-700">¥{pkg.price}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Transaction History */}
        <div>
          <h2 className="app-section-title">{t("transactionHistory")}</h2>
          <div className="app-surface mt-4 overflow-hidden">
            {(!transactions || transactions.length === 0) ? (
              <AppEmptyState
                title={t("noTransactions")}
                icon={<CreditCard className="h-5 w-5" />}
              />
            ) : (
              <table className="w-full">
                <thead className="bg-stone-50/80">
                  <tr className="border-b border-stone-200 text-left text-sm text-stone-500">
                    <th className="px-6 py-3">{t("typeCol")}</th>
                    <th className="px-6 py-3">{t("creditsCol")}</th>
                    <th className="px-6 py-3">{t("descriptionCol")}</th>
                    <th className="px-6 py-3">{t("timeCol")}</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((tx: { id: string; type: string; amount: number; description: string; created_at: string }) => (
                    <tr key={tx.id} className="border-b border-stone-100 last:border-0">
                      <td className="px-6 py-3">
                        <span
                          className={`rounded-full px-2.5 py-1 text-xs font-semibold uppercase tracking-[0.12em] ${
                            tx.type === "consume"
                              ? "bg-red-100 text-red-700"
                              : "bg-emerald-100 text-emerald-700"
                          }`}
                        >
                          {tx.type === "consume" ? t("consume") : t("rechargeType")}
                        </span>
                      </td>
                      <td className="px-6 py-3 font-medium">
                        {tx.type === "consume" ? "-" : "+"}
                        {tx.amount}
                      </td>
                      <td className="px-6 py-3 text-sm text-stone-600">
                        {tx.description}
                      </td>
                      <td className="px-6 py-3 text-sm text-stone-500">
                        {new Date(tx.created_at).toLocaleDateString("zh-CN")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        <PaymentDialog
          open={showPayment}
          onOpenChange={setShowPayment}
        />
      </AppPageShell>
    </MainLayout>
  )
}
