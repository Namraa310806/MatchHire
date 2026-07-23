import api from '@/lib/api'

export interface Recommendation {
  id: string
  type: 'job' | 'candidate'
  score: number
  reasons: string[]
  data: any
  createdAt: string
}

export interface JobRecommendation extends Recommendation {
  type: 'job'
  data: {
    jobId: string
    title: string
    company: string
    location: string
    salary: { min: number; max: number }
    matchScore: number
  }
}

export interface CandidateRecommendation extends Recommendation {
  type: 'candidate'
  data: {
    candidateId: string
    name: string
    email: string
    skills: string[]
    experience: string
    matchScore: number
  }
}

export const recommendationService = {
  getJobRecommendations: async (candidateId: string): Promise<JobRecommendation[]> => {
    const response = await api.get(`/recommendations/jobs/${candidateId}`)
    return response.data
  },

  getCandidateRecommendations: async (jobId: string): Promise<CandidateRecommendation[]> => {
    const response = await api.get(`/recommendations/candidates/${jobId}`)
    return response.data
  },

  updatePreferences: async (candidateId: string, preferences: {
    preferredLocations?: string[]
    preferredJobTypes?: string[]
    preferredSkills?: string[]
    salaryExpectation?: { min: number; max: number }
  }): Promise<void> => {
    await api.put(`/recommendations/preferences/${candidateId}`, preferences)
  },

  getPreferences: async (candidateId: string): Promise<any> => {
    const response = await api.get(`/recommendations/preferences/${candidateId}`)
    return response.data
  },

  dismissRecommendation: async (recommendationId: string): Promise<void> => {
    await api.post(`/recommendations/${recommendationId}/dismiss`)
  },

  saveRecommendation: async (recommendationId: string): Promise<void> => {
    await api.post(`/recommendations/${recommendationId}/save`)
  },
}
