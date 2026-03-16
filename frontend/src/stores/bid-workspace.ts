import { create } from "zustand"
import type { BidStep } from "@/types"

export type ChatMode = "sidebar" | "fullscreen"

const STEP_ORDER: BidStep[] = [
  "upload",
  "overview",
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
  chatMode: ChatMode

  // Legacy aliases
  isChatOpen: boolean

  setProject: (id: string, institution: string) => void
  initSteps: (completed: BidStep[], current: BidStep) => void
  goToStep: (step: BidStep) => void
  completeStep: (step: BidStep) => void
  toggleChatPanel: () => void
  setChatMode: (mode: ChatMode) => void
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
  chatMode: "sidebar",
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

  initSteps: (completed, current) =>
    set({ completedSteps: completed, currentStep: current }),

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

  setChatMode: (mode) =>
    set({
      chatMode: mode,
      isChatPanelOpen: true,
      isChatOpen: true,
    }),

  reset: () =>
    set({
      projectId: null,
      institution: null,
      currentStep: "upload",
      completedSteps: [],
      chatMode: "sidebar",
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
