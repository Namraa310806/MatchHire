import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobService, JobSearchParams, JobApplyRequest } from '../services/jobService';
import { toast } from 'sonner';

export const useJobs = (params?: JobSearchParams) => {
  return useQuery({
    queryKey: ['jobs', params],
    queryFn: () => jobService.getJobs(params),
  });
};

export const useJob = (id: string) => {
  return useQuery({
    queryKey: ['jobs', id],
    queryFn: () => jobService.getJob(id),
    enabled: !!id,
  });
};

export const useApplyToJob = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ jobId, data }: { jobId: string; data: JobApplyRequest }) => 
      jobService.applyToJob(jobId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      toast.success('Application submitted successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to submit application');
    },
  });
};

export const useJobMatch = (jobId: string) => {
  return useQuery({
    queryKey: ['jobs', jobId, 'match'],
    queryFn: () => jobService.getJobMatch(jobId),
    enabled: !!jobId,
  });
};

export const useSearchJobs = (params: JobSearchParams) => {
  return useQuery({
    queryKey: ['jobs', 'search', params],
    queryFn: () => jobService.searchJobs(params),
    enabled: !!(params.query || params.location || params.skills),
  });
};
