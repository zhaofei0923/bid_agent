import apiClient from "./api-client"
import type { CreditTransaction, RechargePackage } from "@/types/credits"

export const creditsService = {
  getBalance: async () => {
    const { data } = await apiClient.get<{ balance: number }>("/payment/balance")
    return data.balance
  },

  listTransactions: async (page = 1, pageSize = 20) => {
    const { data } = await apiClient.get<CreditTransaction[]>(
      "/payment/transactions",
      { params: { page, page_size: pageSize } }
    )
    return data
  },

  listPackages: async () => {
    const { data } = await apiClient.get<RechargePackage[]>("/payment/packages")
    return data
  },

  createOrder: async (packageId: string, paymentMethod = "alipay") => {
    const { data } = await apiClient.post("/payment/orders", {
      package_id: packageId,
      payment_method: paymentMethod,
    })
    return data
  },

  deduct: async (amount: number, description: string) => {
    const { data } = await apiClient.post<{ balance: number }>(
      "/payment/credits/deduct",
      { amount, description }
    )
    return data.balance
  },

  recharge: async (amount: number, description = "manual_recharge") => {
    const { data } = await apiClient.post<{ balance: number }>(
      "/payment/credits/recharge",
      { amount, description }
    )
    return data.balance
  },
}
