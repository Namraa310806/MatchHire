import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../services/adminService';
import type { AdminJobUpdate, JobListParams } from '../types';

export function useAdminJobs(params: JobListParams = {}) {
  return useQuery({
    queryKey: ['admin', 'jobs', params],
    queryFn: () => adminApi.getJobs(params),
  });
}

export function useUpdateJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, update }: { id: string; update: AdminJobUpdate }) =>
      adminApi.updateJob(id, update),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'jobs'] });
    },
  });
}
