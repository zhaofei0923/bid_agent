import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { documentService } from "@/services/documents"

export function useDocuments(projectId: string) {
  return useQuery({
    queryKey: ["documents", projectId],
    queryFn: () => documentService.list(projectId),
    enabled: !!projectId,
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
