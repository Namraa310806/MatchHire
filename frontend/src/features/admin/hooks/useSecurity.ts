import { useQuery } from '@tanstack/react-query';
import { securityApi } from '../services/adminService';

export function useSecurityEvents() {
  return useQuery({
    queryKey: ['admin', 'security-events'],
    queryFn: securityApi.getSecurityEvents,
    refetchInterval: 60000, // Refresh every minute
  });
}

export function useLoginActivity() {
  return useQuery({
    queryKey: ['admin', 'login-activity'],
    queryFn: securityApi.getLoginActivity,
    refetchInterval: 120000, // Refresh every 2 minutes
  });
}
