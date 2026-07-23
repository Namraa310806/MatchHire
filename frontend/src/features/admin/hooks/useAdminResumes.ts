import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../services/adminService';
import type { AdminResumeUpdate, ResumeListParams } from '../types';

export function useAdminResumes(params: ResumeListParams = {}) {
  return useQuery({
    queryKey: ['admin', 'resumes', params],
    queryFn: () => adminApi.getResumes(params),
  });
}

export function useUpdateResume() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, update }: { id: string; update: AdminResumeUpdate }) =>
      adminApi.updateResume(id, update),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'resumes'] });
    },
  });
}
