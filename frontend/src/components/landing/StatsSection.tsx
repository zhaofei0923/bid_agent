"use client"

import { useState, useEffect, useRef } from "react"
import { useTranslations } from "next-intl"

function CountUp({ target, suffix }: { target: number; suffix: string }) {
  const [count, setCount] = useState(0)
  const ref = useRef<HTMLDivElement>(null)
  const [started, setStarted] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !started) setStarted(true)
      },
      { threshold: 0.5 }
    )
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [started])

  useEffect(() => {
    if (!started) return
    const duration = 2000
    const steps = 60
    const increment = target / steps
    let current = 0
    const timer = setInterval(() => {
      current += increment
      if (current >= target) {
        setCount(target)
        clearInterval(timer)
      } else {
        setCount(Math.floor(current))
      }
    }, duration / steps)
    return () => clearInterval(timer)
  }, [started, target])

  return (
    <div ref={ref} className="text-4xl font-bold">
      {count}
      {suffix}
    </div>
  )
}

export function StatsSection() {
  const t = useTranslations("landing")
  const stats = t.raw("stats") as Array<{ value: number; suffix: string; label: string; desc: string }>

  return (
    <section className="py-20 bg-slate-900 text-white">
      <div className="container">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <CountUp target={stat.value} suffix={stat.suffix} />
              <p className="mt-2 font-medium">{stat.label}</p>
              <p className="mt-1 text-sm text-slate-400">{stat.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
