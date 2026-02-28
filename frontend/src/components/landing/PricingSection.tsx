"use client"

import Link from "next/link"
import { useTranslations } from "next-intl"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export function PricingSection({ locale }: { locale: string }) {
  const t = useTranslations("landing")
  const plans = t.raw("plans") as Array<{
    name: string
    price: string
    badge?: string
    features: string[]
    cta: string
  }>

  return (
    <section id="pricing" className="py-20">
      <div className="container">
        <h2 className="text-3xl font-bold text-center mb-12">
          {t("pricingTitle")}
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          {plans.map((plan, i) => {
            const highlight = i === 1
            return (
              <Card
                key={plan.name}
                className={`relative ${
                  highlight ? "ring-2 ring-primary shadow-lg" : ""
                }`}
              >
                {plan.badge && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge>{plan.badge}</Badge>
                  </div>
                )}
                <CardHeader className="text-center pt-8">
                  <h3 className="text-lg font-semibold">{plan.name}</h3>
                  <p className="text-3xl font-bold mt-2">{plan.price}</p>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 mb-6">
                    {plan.features.map((f) => (
                      <li key={f} className="text-sm flex items-center gap-2">
                        <span className="text-primary text-xs">✓</span> {f}
                      </li>
                    ))}
                  </ul>
                  <Link href={`/${locale}/auth/register`} className="block">
                    <Button
                      variant={highlight ? "default" : "outline"}
                      className="w-full"
                    >
                      {plan.cta}
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </div>
    </section>
  )
}
