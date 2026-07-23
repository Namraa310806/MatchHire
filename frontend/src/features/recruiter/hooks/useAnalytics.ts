import { useQuery } from '@tanstack/react-query';
import { analyticsService } from '../services';

export const useHiringFunnel = (jobId?: string) => {
  return useQuery({
    queryKey: ['analytics', 'funnel', jobId],
    queryFn: () => analyticsService.getHiringFunnel(jobId),
  });
};

export const useTimeToHire = (jobId?: string) => {
  return useQuery({
    queryKey: ['analytics', 'time-to-hire', jobId],
    queryFn: () => analyticsService.getTimeToHire(jobId),
  });
};

export const useApplicationTrends = (days: number = 30) => {
  return useQuery({
    queryKey: ['analytics', 'application-trends', days],
    queryFn: () => analyticsService.getApplicationTrends(days),
  });
};

export const useJobPerformance = () => {
  return useQuery({
    queryKey: ['analytics', 'job-performance'],
    queryFn: analyticsService.getJobPerformance,
  });
};

export const useSearchPerformance = () => {
  return useQuery({
    queryKey: ['analytics', 'search-performance'],
    queryFn: analyticsService.getSearchPerformance,
  });
};

export const useRecommendationEffectiveness = () => {
  return useQuery({
    queryKey: ['analytics', 'recommendation-effectiveness'],
    queryFn: analyticsService.getRecommendationEffectiveness,
  });
};

export const useInterviewConversion = (jobId?: string) => {
  return useQuery({
    queryKey: ['analytics', 'interview-conversion', jobId],
    queryFn: () => analyticsService.getInterviewConversion(jobId),
  });
};

export const useRecruiterActivity = (days: number = 30) => {
  return useQuery({
    queryKey: ['analytics', 'recruiter-activity', days],
    queryFn: () => analyticsService.getRecruiterActivity(days),
  });
};

export const usePipelineAnalytics = (jobId?: string) => {
  return useQuery({
    queryKey: ['analytics', 'pipeline', jobId],
    queryFn: () => analyticsService.getPipelineAnalytics(jobId),
  });
};

export const useOfferConversion = () => {
  return useQuery({
    queryKey: ['analytics', 'offer-conversion'],
    queryFn: analyticsService.getOfferConversion,
  });
};
