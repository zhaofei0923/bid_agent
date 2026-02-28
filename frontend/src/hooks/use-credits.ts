import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { creditsService } from "@/services/credits"

export function useCreditsBalance() {
  return useQuery({
    queryKey: ["credits-balance"],
    queryFn: () => creditsService.getBalance(),
    staleTime: 30_000,
  })
}

export function useCreditsTransactions(page = 1) {
  return useQuery({
    queryKey: ["credits-transactions", page],
    queryFn: () => creditsService.listTransactions(page),
  })
}

export function useRechargePackages() {
  return useQuery({
    queryKey: ["recharge-packages"],
    queryFn: () => creditsService.listPackages(),
    staleTime: 300_000,
  })
}

export function useCreateOrder() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      packageId,
      paymentMethod,
    }: {
      packageId: string
      paymentMethod?: string
    }) => creditsService.createOrder(packageId, paymentMethod),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["credits-balance"] })
    },
  })
}
