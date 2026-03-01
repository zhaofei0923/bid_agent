import type { ReactNode } from "react"

interface PreviewSectionProps {
  eyebrow: string
  title: string
  children: ReactNode
}

export function PreviewSection({
  eyebrow,
  title,
  children,
}: PreviewSectionProps) {
  return (
    <section className="app-panel px-6 py-8 sm:px-8">
      <p className="app-page-kicker">{eyebrow}</p>
      <h2 className="app-section-title mt-4">{title}</h2>
      <div className="mt-6">{children}</div>
    </section>
  )
}
