import { useQuery } from '@tanstack/react-query';
import { adminApi } from '../services/adminService';
import type { ApplicationListParams } from '../types';

export function useAdminApplications(params: ApplicationListParams = {}) {
  return useQuery({
    queryKey: ['admin', 'applications', params],
    queryFn: () => adminApi.getApplications(params),
  });
}
