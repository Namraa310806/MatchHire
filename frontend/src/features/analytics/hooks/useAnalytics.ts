import { useQuery } from '@tanstack/react-query';
import { analyticsService } from '../services/analyticsService';

export const useCandidateDashboard = () => {
  return useQuery({
    queryKey: ['analytics', 'candidate', 'dashboard'],
    queryFn: analyticsService.getCandidateDashboard,
    refetchOnWindowFocus: false,
  });
};
