import apiClient from "./api-client"
import type {
  Project,
  ProjectCreate,
  ProjectUpdate,
  PaginatedResult,
} from "@/types"

export const projectService = {
  async list(
    params: { page?: number; page_size?: number } = {}
  ): Promise<PaginatedResult<Project>> {
    const res = await apiClient.get<PaginatedResult<Project>>("/projects", {
      params,
    })
    return res.data
  },

  async getById(id: string): Promise<Project> {
    const res = await apiClient.get<Project>(`/projects/${id}`)
    return res.data
  },

  async create(data: ProjectCreate): Promise<Project> {
    const res = await apiClient.post<Project>("/projects", data)
    return res.data
  },

  async update(id: string, data: ProjectUpdate): Promise<Project> {
    const res = await apiClient.put<Project>(`/projects/${id}`, data)
    return res.data
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/projects/${id}`)
  },
}
