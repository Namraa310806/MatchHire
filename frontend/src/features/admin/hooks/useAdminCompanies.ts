import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../services/adminService';
import type { AdminCompanyUpdate, CompanyListParams } from '../types';

export function useAdminCompanies(params: CompanyListParams = {}) {
  return useQuery({
    queryKey: ['admin', 'companies', params],
    queryFn: () => adminApi.getCompanies(params),
  });
}

export function useUpdateCompany() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, update }: { id: string; update: AdminCompanyUpdate }) =>
      adminApi.updateCompany(id, update),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'companies'] });
    },
  });
}
