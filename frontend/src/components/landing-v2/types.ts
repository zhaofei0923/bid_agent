export interface LandingV2Institution {
  name: string
  detail: string
}

export interface LandingV2OutcomeItem {
  title: string
  desc: string
  bullets: string[]
}

export interface LandingV2WorkflowStep {
  name: string
  detail: string
  outcome: string
}

export interface LandingV2CapabilityItem {
  title: string
  desc: string
  stat: string
  statLabel: string
}

export interface LandingV2RoleItem {
  role: string
  summary: string
  headline: string
  bullets: string[]
}

export interface LandingV2PlanItem {
  name: string
  price: string
  period: string
  summary: string
  cta: string
  highlight?: string
  features: string[]
}
