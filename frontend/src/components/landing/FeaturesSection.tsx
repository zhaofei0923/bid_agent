"use client"

import { useTranslations } from "next-intl"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Search, BrainCircuit, Lightbulb, CheckCircle2 } from "lucide-react"

const FEATURE_ICONS = [Search, BrainCircuit, Lightbulb, CheckCircle2]
const FEATURE_COLORS = ["border-l-blue-500", "border-l-purple-500", "border-l-green-500", "border-l-orange-500"]
const ICON_COLORS = ["text-blue-500", "text-purple-500", "text-green-500", "text-orange-500"]
const ICON_BG_COLORS = ["bg-blue-50", "bg-purple-50", "bg-green-50", "bg-orange-50"]

export function FeaturesSection() {
  const t = useTranslations("landing")
  const featureItems = t.raw("featureItems") as Array<{ title: string; desc: string }>

  return (
    <section id="features" className="py-20 bg-muted/30">
      <div className="container">
        <h2 className="text-3xl font-bold text-center mb-12">
          {t("featuresTitle")}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {featureItems.map((feat, i) => {
            const Icon = FEATURE_ICONS[i]
            return (
              <Card
                key={feat.title}
                className={`border-l-4 ${FEATURE_COLORS[i]} hover:-translate-y-1 hover:shadow-lg transition-all duration-200`}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-4">
                    <div className={`p-2.5 rounded-lg ${ICON_BG_COLORS[i]}`}>
                      <Icon className={`h-6 w-6 ${ICON_COLORS[i]}`} />
                    </div>
                    <h3 className="text-lg font-semibold">{feat.title}</h3>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground leading-relaxed">{feat.desc}</p>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </div>
    </section>
  )
}
