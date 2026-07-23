import { useQuery } from '@tanstack/react-query';
import { auditLogsApi } from '../services/adminService';
import type { AuditLogFilters } from '../types';

export function useAuditLogs(filters: AuditLogFilters = {}) {
  return useQuery({
    queryKey: ['admin', 'audit-logs', filters],
    queryFn: () => auditLogsApi.getAuditLogs(filters),
  });
}
