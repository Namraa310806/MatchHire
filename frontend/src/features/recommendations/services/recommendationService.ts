import api from '@/lib/api';
import { Job } from '@/types';

export interface JobRecommendation {
  job: Job;
  score: number;
  explanation?: string;
  signals?: Record<string, number>;
  match_reasons?: string[];
}

export interface RecommendationFeedback {
  recommendation_id: string;
  helpful: boolean;
  feedback_text?: string;
}

export const recommendationService = {
  // Get job recommendations for candidate
  getJobRecommendations: async (): Promise<JobRecommendation[]> => {
    const response = await api.get('/matching/jobs/recommendations/');
    return response.data;
  },

  // Submit feedback on recommendation
  submitFeedback: async (data: RecommendationFeedback): Promise<void> => {
    await api.post('/matching/jobs/recommendations/feedback/', data);
  },
};
