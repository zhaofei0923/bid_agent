"use client"

import Link from "next/link"
import { useTranslations } from "next-intl"
import { Button } from "@/components/ui/button"

export function CTASection({ locale }: { locale: string }) {
  const t = useTranslations("landing")

  return (
    <section className="py-24 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
      <div className="container text-center">
        <h2 className="text-3xl md:text-4xl font-bold mb-4">
          {t("ctaTitle")}
        </h2>
        <p className="text-lg text-white/80 mb-8">
          {t("ctaDesc")}
        </p>
        <Link href={`/${locale}/auth/register`}>
          <Button
            size="lg"
            variant="outline"
            className="bg-white text-blue-600 hover:bg-white/90 border-white"
          >
            {t("ctaButton")}
          </Button>
        </Link>
      </div>
    </section>
  )
}
