import apiClient from "./api-client"
import type { BidPlan, BidPlanTask } from "@/types/bid"

export const bidPlanService = {
  getByProject: async (projectId: string) => {
    const { data } = await apiClient.get<BidPlan>(
      `/projects/${projectId}/plan`
    )
    return data
  },

  createOrUpdate: async (
    projectId: string,
    plan: { outline?: Record<string, unknown>; strategy?: Record<string, unknown> }
  ) => {
    const { data } = await apiClient.post<BidPlan>(
      `/projects/${projectId}/plan`,
      plan
    )
    return data
  },

  listTasks: async (projectId: string) => {
    const { data } = await apiClient.get<BidPlanTask[]>(
      `/projects/${projectId}/plan/tasks`
    )
    return data
  },

  addTask: async (projectId: string, task: Partial<BidPlanTask>) => {
    const { data } = await apiClient.post<BidPlanTask>(
      `/projects/${projectId}/plan/tasks`,
      task
    )
    return data
  },

  /** Update status only (legacy PUT). */
  updateTask: async (
    projectId: string,
    taskId: string,
    status: string
  ) => {
    const { data } = await apiClient.put<BidPlanTask>(
      `/projects/${projectId}/plan/tasks/${taskId}/status`,
      null,
      { params: { status } }
    )
    return data
  },

  /** Update any task fields (PATCH). */
  updateTaskFields: async (
    projectId: string,
    taskId: string,
    fields: Partial<Pick<BidPlanTask, "title" | "description" | "category" | "priority" | "due_date" | "assigned_to" | "notes" | "related_document" | "reference_page" | "sort_order" | "status">>
  ) => {
    const { data } = await apiClient.patch<BidPlanTask>(
      `/projects/${projectId}/plan/tasks/${taskId}`,
      fields
    )
    return data
  },

  /** Reorder tasks by ID sequence. */
  reorderTasks: async (projectId: string, taskIds: string[]) => {
    await apiClient.post(
      `/projects/${projectId}/plan/reorder`,
      { task_ids: taskIds }
    )
  },

  deleteTask: async (projectId: string, taskId: string) => {
    await apiClient.delete(`/projects/${projectId}/plan/tasks/${taskId}`)
  },

  generatePlan: async (projectId: string) => {
    const { data } = await apiClient.post<{ plan: BidPlan; tasks: BidPlanTask[] }>(
      `/projects/${projectId}/plan/generate`,
      undefined,
      { timeout: 150_000 } // LLM can take up to 120s; allow 150s
    )
    return data
  },

  /** Force-regenerate plan (deletes existing tasks and re-generates). */
  regeneratePlan: async (projectId: string) => {
    const { data } = await apiClient.post<{ plan: BidPlan; tasks: BidPlanTask[] }>(
      `/projects/${projectId}/plan/generate`,
      undefined,
      { timeout: 150_000, params: { force: true } }
    )
    return data
  },
}
