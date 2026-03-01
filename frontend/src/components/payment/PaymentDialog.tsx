"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { useMutation, useQuery } from "@tanstack/react-query"
import { creditsService } from "@/services/credits"
import type { RechargePackage } from "@/types/credits"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

interface PaymentDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
}

export default function PaymentDialog({ open, onOpenChange, onSuccess }: PaymentDialogProps) {
  const t = useTranslations("payment")
  const tc = useTranslations("common")
  const tCredits = useTranslations("credits")
  const [selectedPackage, setSelectedPackage] = useState<string>("")
  const [paymentMethod, setPaymentMethod] = useState<string>("alipay")

  const { data: packages } = useQuery({
    queryKey: ["credits", "packages"],
    queryFn: () => creditsService.listPackages(),
    enabled: open,
  })

  const createOrderMutation = useMutation({
    mutationFn: (packageId: string) =>
      creditsService.createOrder(packageId, paymentMethod),
    onSuccess: () => {
      onSuccess?.()
      onOpenChange(false)
    },
  })

  const pkgList: RechargePackage[] = packages ?? []
  const selectedPkg = pkgList.find((p) => p.id === selectedPackage)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{t("title")}</DialogTitle>
        </DialogHeader>

        {/* Package Selection */}
        <div className="space-y-3">
          <label className="text-sm font-medium text-stone-700">{t("selectPackage")}</label>
          <div className="space-y-2">
            {pkgList.map((pkg) => (
              <button
                key={pkg.id}
                onClick={() => setSelectedPackage(pkg.id)}
                className={`w-full rounded-[24px] border p-4 text-left transition ${
                  selectedPackage === pkg.id
                    ? "border-slate-900 bg-stone-50 ring-1 ring-slate-900"
                    : "border-stone-200 hover:border-stone-300"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-medium">{pkg.name}</span>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-slate-900">¥{pkg.price}</p>
                    <p className="text-xs text-stone-500">{pkg.credits} {tCredits("creditsUnit")}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Payment Method */}
        <div className="mt-4 space-y-3">
          <label className="text-sm font-medium text-stone-700">{t("paymentMethod")}</label>
          <div className="flex gap-3">
            {[
              { id: "alipay", name: t("alipay"), icon: "💳" },
              { id: "wechat", name: t("wechatPay"), icon: "💚" },
            ].map((method) => (
              <button
                key={method.id}
                onClick={() => setPaymentMethod(method.id)}
                className={`flex-1 rounded-[22px] border p-3 text-center transition ${
                  paymentMethod === method.id
                    ? "border-slate-900 bg-stone-50"
                    : "border-stone-200 hover:border-stone-300"
                }`}
              >
                <span className="text-xl">{method.icon}</span>
                <p className="mt-1 text-sm">{method.name}</p>
              </button>
            ))}
          </div>
        </div>

        <DialogFooter>
          <Button onClick={() => onOpenChange(false)} variant="outline">
            {tc("cancel")}
          </Button>
          <Button
            onClick={() => selectedPackage && createOrderMutation.mutate(selectedPackage)}
            disabled={createOrderMutation.isPending || !selectedPackage}
          >
            {createOrderMutation.isPending
              ? tc("processing")
              : t("pay", { amount: selectedPkg?.price ?? 0 })}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
