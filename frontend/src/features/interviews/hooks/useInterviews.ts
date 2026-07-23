import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { interviewService } from '../services/interviewService';
import { toast } from 'sonner';

export const useApplicationInterviews = (applicationId: string) => {
  return useQuery({
    queryKey: ['interviews', 'application', applicationId],
    queryFn: () => interviewService.getApplicationInterviews(applicationId),
    enabled: !!applicationId,
  });
};

export const useMyInterviews = () => {
  return useQuery({
    queryKey: ['interviews', 'my'],
    queryFn: interviewService.getMyInterviews,
  });
};

export const useInterview = (interviewId: string) => {
  return useQuery({
    queryKey: ['interviews', interviewId],
    queryFn: () => interviewService.getInterview(interviewId),
    enabled: !!interviewId,
  });
};

export const useInterviewDetails = (interviewId: string) => {
  return useQuery({
    queryKey: ['interviews', interviewId, 'details'],
    queryFn: () => interviewService.getInterview(interviewId),
    enabled: !!interviewId,
  });
};

export const useUpdateInterviewStatus = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => 
      interviewService.updateInterviewStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interviews'] });
      toast.success('Interview status updated successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to update interview status');
    },
  });
};

export const useInterviewHistory = (interviewId: string) => {
  return useQuery({
    queryKey: ['interviews', interviewId, 'history'],
    queryFn: () => interviewService.getInterviewHistory(interviewId),
    enabled: !!interviewId,
  });
};
