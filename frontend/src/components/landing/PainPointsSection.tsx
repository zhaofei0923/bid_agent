"use client"

import { useTranslations } from "next-intl"
import { Card, CardContent, CardHeader } from "@/components/ui/card"

const PAIN_POINT_ICONS = ["⏰", "📋", "⚠️", "🔍", "📚", "👥"]

export function PainPointsSection() {
  const t = useTranslations("landing")
  const painPoints = t.raw("painPoints") as Array<{ title: string; desc: string }>

  return (
    <section className="py-20">
      <div className="container">
        <h2 className="text-3xl font-bold text-center mb-12">
          {t("painPointsTitle")}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {painPoints.map((item, i) => (
            <Card key={item.title} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-2">
                <div className="text-2xl mb-1">{PAIN_POINT_ICONS[i]}</div>
                <h3 className="font-semibold">{item.title}</h3>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{item.desc}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
