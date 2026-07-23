import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { applicationService } from '../services/applicationService';
import { toast } from 'sonner';

export const useMyApplications = () => {
  return useQuery({
    queryKey: ['applications', 'my'],
    queryFn: applicationService.getMyApplications,
  });
};

export const useApplication = (id: string) => {
  return useQuery({
    queryKey: ['applications', id],
    queryFn: () => applicationService.getApplication(id),
    enabled: !!id,
  });
};

export const useWithdrawApplication = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => applicationService.withdrawApplication(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] });
      queryClient.invalidateQueries({ queryKey: ['applications', 'my'] });
      toast.success('Application withdrawn successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to withdraw application');
    },
  });
};

export const useApplicationHistory = (id: string) => {
  return useQuery({
    queryKey: ['applications', id, 'history'],
    queryFn: () => applicationService.getApplicationHistory(id),
    enabled: !!id,
  });
};
