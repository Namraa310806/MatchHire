import { useQuery } from '@tanstack/react-query';
import { recruiterService } from '../services';

export const useDashboardStats = () => {
  return useQuery({
    queryKey: ['recruiter', 'dashboard', 'stats'],
    queryFn: recruiterService.getDashboardStats,
  });
};

export const useRecentActivity = () => {
  return useQuery({
    queryKey: ['recruiter', 'dashboard', 'activity'],
    queryFn: recruiterService.getRecentActivity,
  });
};
