import { useQuery } from '@tanstack/react-query';
import { healthApi } from '../services/adminService';

export function useHealthStatus() {
  return useQuery({
    queryKey: ['health', 'status'],
    queryFn: healthApi.getHealthStatus,
    refetchInterval: 30000, // Auto-refresh every 30 seconds
    staleTime: 10000,
  });
}

export function useReadiness() {
  return useQuery({
    queryKey: ['health', 'readiness'],
    queryFn: healthApi.getReadiness,
    refetchInterval: 10000, // Check readiness every 10 seconds
    staleTime: 5000,
  });
}
