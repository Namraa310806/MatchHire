import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { recommendationService } from '../services';

export const useMatchingCandidates = (jobId: string) => {
  return useQuery({
    queryKey: ['recommendations', 'job', jobId],
    queryFn: () => recommendationService.getMatchingCandidates(jobId),
    enabled: !!jobId,
  });
};

export const useRecommendedCandidates = () => {
  return useQuery({
    queryKey: ['recommendations', 'candidates'],
    queryFn: recommendationService.getRecommendedCandidates,
  });
};

export const useSimilarCandidates = (candidateId: string) => {
  return useQuery({
    queryKey: ['candidates', candidateId, 'similar'],
    queryFn: () => recommendationService.getSimilarCandidates(candidateId),
    enabled: !!candidateId,
  });
};

export const useRecentlyActiveCandidates = () => {
  return useQuery({
    queryKey: ['candidates', 'recently-active'],
    queryFn: recommendationService.getRecentlyActiveCandidates,
  });
};

export const useTrendingCandidates = () => {
  return useQuery({
    queryKey: ['candidates', 'trending'],
    queryFn: recommendationService.getTrendingCandidates,
  });
};

export const useProvideFeedback = () => {
  return useMutation({
    mutationFn: ({
      recommendationId,
      feedback,
    }: {
      recommendationId: string;
      feedback: 'positive' | 'negative';
    }) => recommendationService.provideFeedback(recommendationId, feedback),
  });
};

export const useSaveCandidate = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (candidateId: string) => recommendationService.saveCandidate(candidateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates', 'saved'] });
    },
  });
};

export const useUnsaveCandidate = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (candidateId: string) =>
      recommendationService.unsaveCandidate(candidateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates', 'saved'] });
    },
  });
};

export const useSavedCandidates = () => {
  return useQuery({
    queryKey: ['candidates', 'saved'],
    queryFn: recommendationService.getSavedCandidates,
  });
};
