"use client"

import Link from "next/link"
import { useTranslations } from "next-intl"
import { Button } from "@/components/ui/button"
import { LayoutDashboard, Sparkles, FileText, ListChecks, ChevronRight } from "lucide-react"

export function HeroSection({ locale }: { locale: string }) {
  const t = useTranslations("landing")

  return (
    <section className="relative pt-32 pb-20 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-slate-50 to-blue-50/50 -z-10" />
      <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-[0.02] -z-10" />

      <div className="container text-center">
        <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight">
          <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-blue-600 bg-clip-text text-transparent">
            {t("heroTitle")}
          </span>
        </h1>

        <p className="mt-6 text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto">
          {t("heroSubtitle", { institutions: "ADB · WB · UN" })}
        </p>

        <div className="mt-8 flex items-center justify-center gap-4">
          <Link href={`/${locale}/auth/register`}>
            <Button size="lg" className="gap-2">
              {t("cta")}
            </Button>
          </Link>
          <a href="#features">
            <Button variant="outline" size="lg">
              {t("ctaSecondary")}
            </Button>
          </a>
        </div>

        <div className="mt-16 mx-auto max-w-5xl">
          <div className="rounded-xl border bg-background/50 shadow-2xl p-2" style={{ perspective: "1000px" }}>
            <div
              className="rounded-lg bg-white border shadow-sm overflow-hidden flex flex-col"
              style={{ transform: "rotateX(2deg)", transformOrigin: "top center" }}
            >
              {/* Mock Header */}
              <div className="h-12 border-b bg-slate-50/80 flex items-center px-4 gap-2">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-400" />
                  <div className="w-3 h-3 rounded-full bg-amber-400" />
                  <div className="w-3 h-3 rounded-full bg-green-400" />
                </div>
                <div className="ml-4 flex items-center gap-2 text-sm text-slate-500 font-medium">
                  <LayoutDashboard className="w-4 h-4" />
                  <span>{t("workspacePreview")}</span>
                  <span className="text-slate-300">|</span>
                  <span className="text-slate-400 font-normal">{t("workspacePreviewDesc")}</span>
                </div>
              </div>

              {/* Mock Body */}
              <div className="flex h-[400px] text-left">
                {/* Left Column: Steps */}
                <div className="w-1/4 border-r bg-slate-50/50 p-4 flex flex-col gap-3">
                  <div className="flex items-center gap-2 text-sm font-medium text-slate-600 mb-2">
                    <ListChecks className="w-4 h-4" />
                    步骤导航
                  </div>
                  <div className="h-10 bg-blue-50 rounded-md border border-blue-200 flex items-center px-3 gap-2 shadow-sm">
                    <div className="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px] font-bold">1</div>
                    <div className="h-2 w-16 bg-blue-300 rounded" />
                  </div>
                  <div className="h-10 bg-white rounded-md border border-slate-100 flex items-center px-3 gap-2">
                    <div className="w-5 h-5 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center text-[10px] font-bold">2</div>
                    <div className="h-2 w-20 bg-slate-200 rounded" />
                  </div>
                  <div className="h-10 bg-white rounded-md border border-slate-100 flex items-center px-3 gap-2">
                    <div className="w-5 h-5 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center text-[10px] font-bold">3</div>
                    <div className="h-2 w-12 bg-slate-200 rounded" />
                  </div>
                  <div className="h-10 bg-white rounded-md border border-slate-100 flex items-center px-3 gap-2">
                    <div className="w-5 h-5 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center text-[10px] font-bold">4</div>
                    <div className="h-2 w-16 bg-slate-200 rounded" />
                  </div>
                </div>

                {/* Middle Column: Editor */}
                <div className="w-1/2 p-8 flex flex-col gap-6 bg-white">
                  <div className="flex items-center gap-2 text-sm font-medium text-slate-600">
                    <FileText className="w-4 h-4" />
                    内容编辑
                  </div>
                  <div className="h-8 w-1/3 bg-slate-100 rounded-md" />
                  <div className="space-y-4 mt-2">
                    <div className="h-3 w-full bg-slate-100 rounded" />
                    <div className="h-3 w-full bg-slate-100 rounded" />
                    <div className="h-3 w-5/6 bg-slate-100 rounded" />
                  </div>
                  <div className="space-y-4 mt-2">
                    <div className="h-3 w-full bg-slate-100 rounded" />
                    <div className="h-3 w-4/5 bg-slate-100 rounded" />
                  </div>
                  <div className="mt-auto flex justify-end">
                    <div className="h-9 w-28 bg-blue-600 rounded-md shadow-sm" />
                  </div>
                </div>

                {/* Right Column: AI Assistant */}
                <div className="w-1/4 border-l bg-blue-50/30 p-4 flex flex-col">
                  <div className="flex items-center gap-2 text-sm font-medium text-blue-700 mb-4">
                    <Sparkles className="w-4 h-4" />
                    AI 助手
                  </div>
                  <div className="flex-1 flex flex-col gap-4">
                    <div className="self-end bg-blue-600 text-white rounded-2xl rounded-tr-sm p-3 w-5/6 shadow-sm">
                      <div className="h-2 w-full bg-blue-400 rounded mb-2" />
                      <div className="h-2 w-2/3 bg-blue-400 rounded" />
                    </div>
                    <div className="self-start bg-white border shadow-sm rounded-2xl rounded-tl-sm p-4 w-11/12">
                      <div className="h-2 w-full bg-slate-200 rounded mb-3" />
                      <div className="h-2 w-full bg-slate-200 rounded mb-3" />
                      <div className="h-2 w-4/5 bg-slate-200 rounded" />
                    </div>
                  </div>
                  <div className="mt-4 h-10 bg-white border rounded-full flex items-center px-4 shadow-sm">
                    <div className="h-2 w-1/2 bg-slate-200 rounded" />
                    <div className="ml-auto w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center">
                      <ChevronRight className="w-3 h-3 text-blue-600" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
