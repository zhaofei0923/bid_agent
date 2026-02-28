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
          <label className="text-sm font-medium text-gray-700">{t("selectPackage")}</label>
          <div className="space-y-2">
            {pkgList.map((pkg) => (
              <button
                key={pkg.id}
                onClick={() => setSelectedPackage(pkg.id)}
                className={`w-full rounded-lg border p-4 text-left transition ${
                  selectedPackage === pkg.id
                    ? "border-blue-500 bg-blue-50 ring-1 ring-blue-500"
                    : "hover:border-gray-300"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-medium">{pkg.name}</span>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-blue-600">¥{pkg.price}</p>
                    <p className="text-xs text-gray-500">{pkg.credits} {tCredits("creditsUnit")}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Payment Method */}
        <div className="mt-4 space-y-3">
          <label className="text-sm font-medium text-gray-700">{t("paymentMethod")}</label>
          <div className="flex gap-3">
            {[
              { id: "alipay", name: t("alipay"), icon: "💳" },
              { id: "wechat", name: t("wechatPay"), icon: "💚" },
            ].map((method) => (
              <button
                key={method.id}
                onClick={() => setPaymentMethod(method.id)}
                className={`flex-1 rounded-lg border p-3 text-center transition ${
                  paymentMethod === method.id
                    ? "border-blue-500 bg-blue-50"
                    : "hover:border-gray-300"
                }`}
              >
                <span className="text-xl">{method.icon}</span>
                <p className="mt-1 text-sm">{method.name}</p>
              </button>
            ))}
          </div>
        </div>

        <DialogFooter>
          <button
            onClick={() => onOpenChange(false)}
            className="rounded-lg border px-4 py-2 text-sm"
          >
            {tc("cancel")}
          </button>
          <button
            onClick={() => selectedPackage && createOrderMutation.mutate(selectedPackage)}
            disabled={createOrderMutation.isPending || !selectedPackage}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white disabled:opacity-50"
          >
            {createOrderMutation.isPending
              ? tc("processing")
              : t("pay", { amount: selectedPkg?.price ?? 0 })}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
