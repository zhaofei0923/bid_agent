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
      <h2 className="app-section-title">{t("creditsPage.title")}</h2>
      <p className="mt-2 text-sm leading-7 text-stone-600">{t("creditsPage.subtitle")}</p>

      {/* Balance */}
      <div className="app-section-frame mt-6 px-6 py-6">
        <p className="app-detail-label">{t("creditsPage.currentBalance")}</p>
        <p className="app-metric-value mt-3">
          {balance ?? user?.credits_balance ?? 0}
        </p>
        <p className="mt-2 text-sm text-stone-500">{tc("credits")}</p>
      </div>

      {/* Usage Tips */}
      <div className="app-section-frame mt-6 px-6 py-6">
        <h3 className="text-base font-semibold text-slate-900">{t("creditsPage.usageTips")}</h3>
        <div className="mt-3 space-y-2 text-sm leading-7 text-stone-600">
          <p>• {t("creditsPage.tip1")}</p>
          <p>• {t("creditsPage.tip2")}</p>
          <p>• {t("creditsPage.tip3")}</p>
          <p>• {t("creditsPage.tip4")}</p>
          <p>• {t("creditsPage.tip5")}</p>
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="app-section-frame mt-6 px-6 py-6">
        <h3 className="text-base font-semibold text-slate-900">{t("creditsPage.recentTransactions")}</h3>
        {(!transactions || transactions.length === 0) ? (
          <p className="mt-3 text-sm text-stone-500">{t("creditsPage.noTransactions")}</p>
        ) : (
          <div className="mt-3 space-y-2">
            {transactions.map((tx: { id: string; type: string; amount: number; description: string; created_at: string }) => (
              <div key={tx.id} className="app-surface-muted flex items-center justify-between px-4 py-3">
                <div>
                  <p className="text-sm font-medium text-slate-900">{tx.description}</p>
                  <p className="text-xs uppercase tracking-[0.12em] text-stone-500">
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
