export interface CreditTransaction {
  id: string
  user_id: string
  amount: number
  balance_after: number
  type: "recharge" | "consume" | "refund"
  description: string
  created_at: string
}

export interface RechargePackage {
  id: string
  name: string
  credits: number
  price: number
  currency: string
  discount_percent: number | null
  is_active: boolean
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
