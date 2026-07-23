import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { interviewService, InterviewCreate, InterviewUpdate } from '../services';

export const useUpcomingInterviews = () => {
  return useQuery({
    queryKey: ['interviews', 'upcoming'],
    queryFn: interviewService.getUpcomingInterviews,
  });
};

export const usePastInterviews = () => {
  return useQuery({
    queryKey: ['interviews', 'past'],
    queryFn: interviewService.getPastInterviews,
  });
};

export const useJobInterviews = (jobId: string) => {
  return useQuery({
    queryKey: ['job', jobId, 'interviews'],
    queryFn: () => interviewService.getJobInterviews(jobId),
    enabled: !!jobId,
  });
};

export const useInterview = (id: string) => {
  return useQuery({
    queryKey: ['interview', id],
    queryFn: () => interviewService.getInterview(id),
    enabled: !!id,
  });
};

export const useCreateInterview = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: InterviewCreate) => interviewService.createInterview(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interviews'] });
      queryClient.invalidateQueries({ queryKey: ['job', 'interviews'] });
    },
  });
};

export const useUpdateInterview = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: InterviewUpdate }) =>
      interviewService.updateInterview(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['interview', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['interviews'] });
    },
  });
};

export const useCancelInterview = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => interviewService.cancelInterview(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interviews'] });
    },
  });
};

export const useCompleteInterview = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, notes }: { id: string; notes?: string }) =>
      interviewService.completeInterview(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interviews'] });
    },
  });
};

export const useRescheduleInterview = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, scheduledAt }: { id: string; scheduledAt: string }) =>
      interviewService.rescheduleInterview(id, scheduledAt),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interviews'] });
    },
  });
};
