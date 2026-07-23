import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobService, JobCreate, JobUpdate } from '../services';

export const useMyJobs = () => {
  return useQuery({
    queryKey: ['recruiter', 'jobs'],
    queryFn: jobService.getMyJobs,
  });
};

export const useJob = (id: string) => {
  return useQuery({
    queryKey: ['job', id],
    queryFn: () => jobService.getJob(id),
    enabled: !!id,
  });
};

export const useCreateJob = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: JobCreate) => jobService.createJob(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recruiter', 'jobs'] });
    },
  });
};

export const useUpdateJob = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: JobUpdate }) =>
      jobService.updateJob(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['recruiter', 'jobs'] });
      queryClient.invalidateQueries({ queryKey: ['job', variables.id] });
    },
  });
};

export const useCloseJob = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => jobService.closeJob(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recruiter', 'jobs'] });
    },
  });
};

export const useDeleteJob = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => jobService.deleteJob(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recruiter', 'jobs'] });
    },
  });
};

export const useDuplicateJob = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => jobService.duplicateJob(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recruiter', 'jobs'] });
    },
  });
};

export const usePublishJob = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => jobService.publishJob(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recruiter', 'jobs'] });
    },
  });
};
