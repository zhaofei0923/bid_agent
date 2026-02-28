import { create } from "zustand"
import type { BidStep } from "@/types"

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

  setProject: (id, institution) => set({ projectId: id, institution }),

  goToStep: (step) => set({ currentStep: step }),

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

  // Legacy
  setCurrentStep: (step) => set({ currentStep: step }),
  toggleChat: () =>
    set((s) => ({
      isChatOpen: !s.isChatOpen,
      isChatPanelOpen: !s.isChatOpen,
    })),
  setChatOpen: (open) => set({ isChatOpen: open, isChatPanelOpen: open }),
}))
