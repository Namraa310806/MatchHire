import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { applicationService, ApplicationStatusUpdate } from '../services';

export const useJobApplications = (jobId: string, status?: string) => {
  return useQuery({
    queryKey: ['job', jobId, 'applications', status],
    queryFn: () => applicationService.getJobApplications(jobId, status),
    enabled: !!jobId,
  });
};

export const useApplication = (id: string) => {
  return useQuery({
    queryKey: ['application', id],
    queryFn: () => applicationService.getApplication(id),
    enabled: !!id,
  });
};

export const useUpdateApplicationStatus = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ApplicationStatusUpdate }) =>
      applicationService.updateApplicationStatus(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['application', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['job', 'applications'] });
    },
  });
};

export const useApplicationHistory = (id: string) => {
  return useQuery({
    queryKey: ['application', id, 'history'],
    queryFn: () => applicationService.getApplicationHistory(id),
    enabled: !!id,
  });
};

export const useBulkUpdateStatus = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      applicationIds,
      status,
    }: {
      applicationIds: string[];
      status: 'submitted' | 'under_review' | 'shortlisted' | 'rejected' | 'hired';
    }) => applicationService.bulkUpdateStatus(applicationIds, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job', 'applications'] });
    },
  });
};

export const useShortlistCandidate = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (applicationId: string) =>
      applicationService.shortlistCandidate(applicationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job', 'applications'] });
    },
  });
};

export const useRejectCandidate = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      applicationId,
      notes,
    }: {
      applicationId: string;
      notes?: string;
    }) => applicationService.rejectCandidate(applicationId, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job', 'applications'] });
    },
  });
};

export const useHireCandidate = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (applicationId: string) =>
      applicationService.hireCandidate(applicationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job', 'applications'] });
    },
  });
};
