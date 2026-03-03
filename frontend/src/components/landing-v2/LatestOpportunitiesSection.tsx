"use client"

import { useTranslations } from "next-intl"
import { LatestOpportunities } from "@/components/opportunities/LatestOpportunities"

export function LatestOpportunitiesSection({ locale }: { locale: string }) {
  const t = useTranslations("landingV2")

  return (
    <section id="opportunities" className="py-20">
      <div className="mx-auto w-full max-w-[1320px] px-6">
        <div className="text-center">
          <p className="landing-v2-kicker">{t("opportunitiesKicker")}</p>
          <h2 className="landing-v2-section-title mt-4">
            {t("opportunitiesTitle")}
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-base leading-relaxed text-stone-500">
            {t("opportunitiesSubtitle")}
          </p>
        </div>

        <div className="mt-12">
          <LatestOpportunities
            locale={locale}
            limit={6}
            linkMode="external"
            showViewAll
          />
        </div>
      </div>
    </section>
  )
}
