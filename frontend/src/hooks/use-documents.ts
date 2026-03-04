import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { documentService } from "@/services/documents"
import type { ProjectDocument } from "@/types/project"

export function useDocumentSections(projectId: string, documentId: string) {
  return useQuery({
    queryKey: ["document-sections", projectId, documentId],
    queryFn: () => documentService.getSections(projectId, documentId),
    enabled: !!projectId && !!documentId,
  })
}

const PROCESSING_STATUSES = new Set(["pending", "processing"])
const SUCCESS_STATUSES = new Set(["processed", "completed"])

export function useDocuments(projectId: string) {
  return useQuery({
    queryKey: ["documents", projectId],
    queryFn: () => documentService.list(projectId),
    enabled: !!projectId,
    // Poll when any doc is processing OR is processed-but-missing ai_overview
    refetchInterval: (query) => {
      const docs = query.state.data as ProjectDocument[] | undefined
      if (!docs) return false
      const hasProcessing = docs.some((d) => PROCESSING_STATUSES.has(d.status))
      const hasPendingAnalysis = docs.some(
        (d) => SUCCESS_STATUSES.has(d.status) && d.ai_overview === null
      )
      return hasProcessing || hasPendingAnalysis ? 3000 : false
    },
  })
}

export function useUploadDocument(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => documentService.upload(projectId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents", projectId] })
    },
  })
}

export function useDeleteDocument(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (documentId: string) =>
      documentService.delete(projectId, documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents", projectId] })
    },
  })
}

export function useAnalyzeDocument(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (documentId: string) =>
      documentService.analyze(projectId, documentId),
    onSuccess: () => {
      // Invalidate so the polling picks up the updated ai_overview
      queryClient.invalidateQueries({ queryKey: ["documents", projectId] })
    },
  })
}
