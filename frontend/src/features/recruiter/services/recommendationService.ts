import api from '@/lib/api';

export interface CandidateRecommendation {
  id: string;
  candidate: string;
  candidate_name?: string;
  candidate_email?: string;
  candidate_profile?: {
    title?: string;
    skills?: string[];
    location?: string;
    experience_years?: number;
  };
  job: string;
  job_title?: string;
  match_score: number;
  explanation?: string;
  signals?: Record<string, number>;
  calculated_at: string;
}

export interface SimilarCandidate {
  id: string;
  candidate: string;
  candidate_name?: string;
  candidate_email?: string;
  similarity_score: number;
  shared_skills?: string[];
  similar_experience?: string[];
}

export const recommendationService = {
  // Get matching candidates for a job
  getMatchingCandidates: async (jobId: string): Promise<CandidateRecommendation[]> => {
    const response = await api.get('/recruiter/candidates/', {
      params: { job_id: jobId },
    });
    return response.data;
  },

  // Get recommended candidates (general)
  getRecommendedCandidates: async (): Promise<CandidateRecommendation[]> => {
    const response = await api.get('/recruiter/recommendations/');
    return response.data;
  },

  // Get similar candidates to a specific candidate
  getSimilarCandidates: async (candidateId: string): Promise<SimilarCandidate[]> => {
    const response = await api.get(`/candidates/${candidateId}/similar/`);
    return response.data;
  },

  // Get recently active candidates
  getRecentlyActiveCandidates: async (): Promise<CandidateRecommendation[]> => {
    const response = await api.get('/recruiter/candidates/recently-active/');
    return response.data;
  },

  // Get trending candidates
  getTrendingCandidates: async (): Promise<CandidateRecommendation[]> => {
    const response = await api.get('/recruiter/candidates/trending/');
    return response.data;
  },

  // Provide feedback on recommendation
  provideFeedback: async (
    recommendationId: string,
    feedback: 'positive' | 'negative'
  ): Promise<void> => {
    await api.post(`/recommendations/${recommendationId}/feedback/`, { feedback });
  },

  // Save candidate
  saveCandidate: async (candidateId: string): Promise<void> => {
    await api.post(`/candidates/${candidateId}/save/`);
  },

  // Unsave candidate
  unsaveCandidate: async (candidateId: string): Promise<void> => {
    await api.delete(`/candidates/${candidateId}/save/`);
  },

  // Get saved candidates
  getSavedCandidates: async (): Promise<CandidateRecommendation[]> => {
    const response = await api.get('/recruiter/candidates/saved/');
    return response.data;
  },
};
