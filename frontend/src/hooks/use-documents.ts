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

export function useDocuments(projectId: string) {
  return useQuery({
    queryKey: ["documents", projectId],
    queryFn: () => documentService.list(projectId),
    enabled: !!projectId,
    // Poll every 3 seconds while any document is still processing
    refetchInterval: (query) => {
      const docs = query.state.data as ProjectDocument[] | undefined
      if (!docs) return false
      const hasProcessing = docs.some((d) => PROCESSING_STATUSES.has(d.status))
      return hasProcessing ? 3000 : false
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
