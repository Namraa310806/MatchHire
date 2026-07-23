import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../services/adminService';
import type { AdminUserUpdate, UserListParams } from '../types';

export function useAdminUsers(params: UserListParams = {}) {
  return useQuery({
    queryKey: ['admin', 'users', params],
    queryFn: () => adminApi.getUsers(params),
  });
}

export function useAdminUser(id: string) {
  return useQuery({
    queryKey: ['admin', 'users', id],
    queryFn: () => adminApi.getUser(id),
    enabled: !!id,
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, update }: { id: string; update: AdminUserUpdate }) =>
      adminApi.updateUser(id, update),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });
}
