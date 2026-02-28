"use client"

import { useTranslations } from "next-intl"
import { useQuery } from "@tanstack/react-query"
import { useAuthStore } from "@/stores/auth"
import { creditsService } from "@/services/credits"

export default function SettingsCreditsPage() {
  const t = useTranslations("settings")
  const tc = useTranslations("common")
  const user = useAuthStore((s) => s.user)

  const { data: balance } = useQuery({
    queryKey: ["credits", "balance"],
    queryFn: () => creditsService.getBalance(),
  })

  const { data: transactions } = useQuery({
    queryKey: ["credits", "transactions", { limit: 5 }],
    queryFn: () => creditsService.listTransactions(1, 5),
  })

  return (
    <div>
      <h2 className="text-lg font-semibold">{t("creditsPage.title")}</h2>
      <p className="mt-1 text-sm text-gray-500">{t("creditsPage.subtitle")}</p>

      {/* Balance */}
      <div className="mt-6 rounded-xl bg-blue-50 p-6">
        <p className="text-sm text-gray-600">{t("creditsPage.currentBalance")}</p>
        <p className="mt-1 text-3xl font-bold text-blue-600">
          {balance ?? user?.credits_balance ?? 0}
        </p>
        <p className="mt-1 text-sm text-gray-500">{tc("credits")}</p>
      </div>

      {/* Usage Tips */}
      <div className="mt-6">
        <h3 className="font-medium">{t("creditsPage.usageTips")}</h3>
        <div className="mt-3 space-y-2 text-sm text-gray-600">
          <p>• {t("creditsPage.tip1")}</p>
          <p>• {t("creditsPage.tip2")}</p>
          <p>• {t("creditsPage.tip3")}</p>
          <p>• {t("creditsPage.tip4")}</p>
          <p>• {t("creditsPage.tip5")}</p>
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="mt-6">
        <h3 className="font-medium">{t("creditsPage.recentTransactions")}</h3>
        {(!transactions || transactions.length === 0) ? (
          <p className="mt-3 text-sm text-gray-500">{t("creditsPage.noTransactions")}</p>
        ) : (
          <div className="mt-3 space-y-2">
            {transactions.map((tx: { id: string; type: string; amount: number; description: string; created_at: string }) => (
              <div key={tx.id} className="flex items-center justify-between rounded-lg border p-3">
                <div>
                  <p className="text-sm font-medium">{tx.description}</p>
                  <p className="text-xs text-gray-500">
                    {new Date(tx.created_at).toLocaleDateString("zh-CN")}
                  </p>
                </div>
                <span
                  className={`font-medium ${
                    tx.type === "consume" ? "text-red-600" : "text-green-600"
                  }`}
                >
                  {tx.type === "consume" ? "-" : "+"}
                  {tx.amount}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
