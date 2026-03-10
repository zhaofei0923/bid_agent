import { create } from "zustand"
import type { BidStep } from "@/types"

const STEP_ORDER: BidStep[] = [
  "upload",
  "overview",
  "analysis",
  "plan",
  "writing",
  "review",
  "tracking",
]

interface BidWorkspaceState {
  projectId: string | null
  institution: string | null
  currentStep: BidStep
  completedSteps: BidStep[]
  isChatPanelOpen: boolean

  // Legacy aliases
  isChatOpen: boolean

  setProject: (id: string, institution: string) => void
  goToStep: (step: BidStep) => void
  completeStep: (step: BidStep) => void
  toggleChatPanel: () => void
  reset: () => void

  // Legacy
  setCurrentStep: (step: BidStep) => void
  toggleChat: () => void
  setChatOpen: (open: boolean) => void
}

export const useBidWorkspaceStore = create<BidWorkspaceState>((set) => ({
  projectId: null,
  institution: null,
  currentStep: "upload",
  completedSteps: [],
  isChatPanelOpen: true,
  isChatOpen: true,

  setProject: (id, institution) =>
    set((s) =>
      s.projectId === id
        ? { institution }
        : {
            projectId: id,
            institution,
            currentStep: "upload",
            completedSteps: [],
          }
    ),

  goToStep: (step) =>
    set((s) => {
      const targetIdx = STEP_ORDER.indexOf(step)
      const currentIdx = STEP_ORDER.indexOf(s.currentStep)
      // Allow going back to completed/current steps, or forward only if previous step is completed
      if (targetIdx <= currentIdx) return { currentStep: step }
      const prevStep = STEP_ORDER[targetIdx - 1]
      if (prevStep && s.completedSteps.includes(prevStep)) return { currentStep: step }
      return {}
    }),

  completeStep: (step) =>
    set((s) => ({
      completedSteps: s.completedSteps.includes(step)
        ? s.completedSteps
        : [...s.completedSteps, step],
    })),

  toggleChatPanel: () =>
    set((s) => ({
      isChatPanelOpen: !s.isChatPanelOpen,
      isChatOpen: !s.isChatPanelOpen,
    })),

  reset: () =>
    set({
      projectId: null,
      institution: null,
      currentStep: "upload",
      completedSteps: [],
    }),

  // Legacy — same validation as goToStep
  setCurrentStep: (step) =>
    set((s) => {
      const targetIdx = STEP_ORDER.indexOf(step)
      const currentIdx = STEP_ORDER.indexOf(s.currentStep)
      if (targetIdx <= currentIdx) return { currentStep: step }
      const prevStep = STEP_ORDER[targetIdx - 1]
      if (prevStep && s.completedSteps.includes(prevStep)) return { currentStep: step }
      return {}
    }),
  toggleChat: () =>
    set((s) => ({
      isChatOpen: !s.isChatOpen,
      isChatPanelOpen: !s.isChatOpen,
    })),
  setChatOpen: (open) => set({ isChatOpen: open, isChatPanelOpen: open }),
}))
