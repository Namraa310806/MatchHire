import { useQuery } from '@tanstack/react-query';
import { adminApi } from '../services/adminService';
import type { AdminDashboardStats } from '../types';

export function useAdminDashboard() {
  return useQuery({
    queryKey: ['admin', 'dashboard'],
    queryFn: adminApi.getDashboardStats,
    refetchInterval: 30000, // Auto-refresh every 30 seconds
    staleTime: 15000,
  });
}
