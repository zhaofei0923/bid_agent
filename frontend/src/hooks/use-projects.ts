import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { projectService } from "@/services/projects"
import type { Project, ProjectCreate, ProjectUpdate } from "@/types"

export function useProjects(params: { page?: number; page_size?: number } = {}) {
  return useQuery({
    queryKey: ["projects", params],
    queryFn: () => projectService.list(params),
  })
}

export function useProject(id: string, pollWhileNoCombined = false) {
  return useQuery({
    queryKey: ["project", id],
    queryFn: () => projectService.getById(id),
    enabled: !!id,
    refetchInterval: pollWhileNoCombined
      ? (query) => {
          const p = query.state.data as Project | undefined
          return !p || p.combined_ai_overview === null ? 3000 : false
        }
      : false,
  })
}

export function useCreateProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: ProjectCreate) => projectService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] })
    },
  })
}

export function useUpdateProject(id: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: ProjectUpdate) => projectService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", id] })
      queryClient.invalidateQueries({ queryKey: ["projects"] })
    },
  })
}

export function useDeleteProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => projectService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] })
    },
  })
}
