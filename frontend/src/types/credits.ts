export interface CreditTransaction {
  id: string
  user_id: string
  amount: number
  balance_after: number
  type: "recharge" | "deduction" | "consume" | "refund"
  description: string
  created_at: string
}

export interface RechargePackage {
  id: string
  name: string
  credits: number
  price: number
  currency: string
  bonus_credits: number
  bonus_description: string | null
  is_active: boolean
  sort_order: number
}

export interface SubscriptionPlan {
  id: string
  name: string
  monthly_credits: number
  price_monthly: number
  price_yearly: number
  features: string[]
  is_active: boolean
}
