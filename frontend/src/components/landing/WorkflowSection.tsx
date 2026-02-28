"use client"

import { useState, useEffect } from "react"
import { useTranslations } from "next-intl"

export function WorkflowSection() {
  const t = useTranslations("landing")
  const steps = t.raw("workflowSteps") as Array<{ label: string; desc: string; tags: string[] }>
  const [activeStep, setActiveStep] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % steps.length)
    }, 5000)
    return () => clearInterval(interval)
  }, [steps.length])

  return (
    <section className="py-20">
      <div className="container">
        <h2 className="text-3xl font-bold text-center mb-12">
          {t("workflowTitle")}
        </h2>

        {/* Step indicators */}
        <div className="flex items-center justify-center gap-2 md:gap-4 mb-10 flex-wrap">
          {steps.map((step, i) => (
            <button
              key={i}
              onClick={() => setActiveStep(i)}
              className="flex flex-col items-center gap-1"
            >
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium transition-all ${
                  i === activeStep
                    ? "bg-primary text-primary-foreground scale-110"
                    : i < activeStep
                      ? "bg-primary/20 text-primary"
                      : "bg-muted text-muted-foreground"
                }`}
              >
                {i + 1}
              </div>
              <span className={`text-xs ${i === activeStep ? "text-primary font-medium" : "text-muted-foreground"}`}>
                {step.label}
              </span>
            </button>
          ))}
        </div>

        {/* Active step content */}
        <div className="max-w-2xl mx-auto rounded-xl border bg-background p-8 shadow-sm">
          <h3 className="text-xl font-semibold mb-3">
            {steps[activeStep].label}
          </h3>
          <p className="text-muted-foreground mb-4">{steps[activeStep].desc}</p>
          <div className="flex gap-2">
            {steps[activeStep].tags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
