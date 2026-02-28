"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { useQuery } from "@tanstack/react-query"
import { creditsService } from "@/services/credits"
import { useAuthStore } from "@/stores/auth"
import PaymentDialog from "@/components/payment/PaymentDialog"
import { MainLayout } from "@/components/layout/MainLayout"

export default function CreditsPage() {
  const t = useTranslations("credits")
  const tc = useTranslations("common")
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
      <div className="container mx-auto px-6 py-8">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">{t("title")}</h1>
          <button
            onClick={() => setShowPayment(true)}
            className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 transition"
          >
            {t("recharge")}
          </button>
        </div>

        {/* Balance Card */}
        <div className="mt-6 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 p-8 text-white">
          <p className="text-sm opacity-80">{t("balance")}</p>
          <p className="mt-2 text-4xl font-bold">
            {balance ?? user?.credits_balance ?? 0}
          </p>
          <p className="mt-1 text-sm opacity-80">{t("creditsUnit")}</p>
        </div>

        {/* Packages */}
        <div className="mt-8">
          <h2 className="text-lg font-semibold">{t("packages")}</h2>
          <div className="mt-4 grid gap-4 md:grid-cols-3">
            {(packages ?? []).map((pkg: { id: string; name: string; credits: number; price: number }) => (
              <div
                key={pkg.id}
                className="rounded-xl border p-6 hover:shadow-md transition cursor-pointer"
                onClick={() => setShowPayment(true)}
              >
                <h3 className="font-semibold">{pkg.name}</h3>
                <p className="mt-2 text-3xl font-bold text-blue-600">
                  {pkg.credits}
                </p>
                <p className="text-sm text-gray-500">{t("creditsUnit")}</p>
                <p className="mt-3 text-lg font-semibold">¥{pkg.price}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Transaction History */}
        <div className="mt-8">
          <h2 className="text-lg font-semibold">{t("transactionHistory")}</h2>
          <div className="mt-4 rounded-xl border bg-white">
            {(!transactions || transactions.length === 0) ? (
              <p className="p-8 text-center text-gray-500">{t("noTransactions")}</p>
            ) : (
              <table className="w-full">
                <thead>
                  <tr className="border-b text-left text-sm text-gray-500">
                    <th className="px-6 py-3">{t("typeCol")}</th>
                    <th className="px-6 py-3">{t("creditsCol")}</th>
                    <th className="px-6 py-3">{t("descriptionCol")}</th>
                    <th className="px-6 py-3">{t("timeCol")}</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((tx: { id: string; type: string; amount: number; description: string; created_at: string }) => (
                    <tr key={tx.id} className="border-b last:border-0">
                      <td className="px-6 py-3">
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs ${
                            tx.type === "consume"
                              ? "bg-red-100 text-red-700"
                              : "bg-green-100 text-green-700"
                          }`}
                        >
                          {tx.type === "consume" ? t("consume") : t("rechargeType")}
                        </span>
                      </td>
                      <td className="px-6 py-3 font-medium">
                        {tx.type === "consume" ? "-" : "+"}
                        {tx.amount}
                      </td>
                      <td className="px-6 py-3 text-sm text-gray-600">
                        {tx.description}
                      </td>
                      <td className="px-6 py-3 text-sm text-gray-500">
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
      </div>
    </MainLayout>
  )
}
