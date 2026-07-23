import api from '@/lib/api'

export interface AnalyticsData {
  period: string
  metrics: {
    totalJobs: number
    totalApplications: number
    totalHires: number
    averageTimeToHire: number
    acceptanceRate: number
  }
  trends: {
    jobsPosted: Array<{ date: string; count: number }>
    applicationsReceived: Array<{ date: string; count: number }>
    hiresMade: Array<{ date: string; count: number }>
  }
  topSkills: Array<{ skill: string; count: number }>
  topLocations: Array<{ location: string; count: number }>
}

export interface CandidateAnalytics {
  profileViews: number
  applicationsSent: number
  interviewRequests: number
  offersReceived: number
  applicationStatus: {
    pending: number
    reviewed: number
    interviewed: number
    offered: number
    rejected: number
  }
  skillMatchScores: Array<{ skill: string; score: number }>
}

export interface RecruiterAnalytics {
  jobsPosted: number
  applicationsReceived: number
  candidatesInterviewed: number
  offersExtended: number
  hiresMade: number
  jobPerformance: Array<{
    jobId: string
    title: string
    applications: number
    interviews: number
    offers: number
    hires: number
  }>
}

export const analyticsService = {
  getPlatformAnalytics: async (period: '7d' | '30d' | '90d' | '1y'): Promise<AnalyticsData> => {
    const response = await api.get('/analytics/platform', { params: { period } })
    return response.data
  },

  getCandidateAnalytics: async (candidateId: string): Promise<CandidateAnalytics> => {
    const response = await api.get(`/analytics/candidate/${candidateId}`)
    return response.data
  },

  getRecruiterAnalytics: async (recruiterId: string, period: '7d' | '30d' | '90d' | '1y'): Promise<RecruiterAnalytics> => {
    const response = await api.get(`/analytics/recruiter/${recruiterId}`, { params: { period } })
    return response.data
  },

  getJobAnalytics: async (jobId: string): Promise<{
    views: number
    applications: number
    interviews: number
    offers: number
    hires: number
    averageTimeToHire: number
    sourceBreakdown: Array<{ source: string; count: number }>
  }> => {
    const response = await api.get(`/analytics/job/${jobId}`)
    return response.data
  },

  exportReport: async (type: 'candidate' | 'recruiter' | 'job', id: string, format: 'pdf' | 'csv'): Promise<Blob> => {
    const response = await api.get(`/analytics/export/${type}/${id}`, {
      params: { format },
      responseType: 'blob'
    })
    return response.data
  },
}
