import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { recommendationService, RecommendationFeedback } from '../services/recommendationService';
import { toast } from 'sonner';

export const useJobRecommendations = () => {
  return useQuery({
    queryKey: ['recommendations', 'jobs'],
    queryFn: recommendationService.getJobRecommendations,
  });
};

export const useSubmitRecommendationFeedback = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: RecommendationFeedback) => recommendationService.submitFeedback(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recommendations'] });
      toast.success('Feedback submitted successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to submit feedback');
    },
  });
};
