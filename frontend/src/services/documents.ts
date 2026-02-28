import apiClient from "./api-client"
import type { ProjectDocument } from "@/types"

export const documentService = {
  async list(projectId: string): Promise<ProjectDocument[]> {
    const res = await apiClient.get<ProjectDocument[]>(
      `/projects/${projectId}/bid-documents`
    )
    return res.data
  },

  async upload(projectId: string, file: File): Promise<ProjectDocument> {
    const formData = new FormData()
    formData.append("file", file)
    const res = await apiClient.post<ProjectDocument>(
      `/projects/${projectId}/bid-documents`,
      formData,
      {
        headers: {
          // Let the browser/Axios set Content-Type with the correct multipart boundary.
          // Do NOT manually set "multipart/form-data" here — it omits the boundary
          // and causes the server to fail parsing the body (Network Error in Axios).
          "Content-Type": undefined,
        },
        // Large file uploads may exceed the default 30s timeout
        timeout: 120_000,
      }
    )
    return res.data
  },
}
