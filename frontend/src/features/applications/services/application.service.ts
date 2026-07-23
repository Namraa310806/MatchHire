import api from '@/lib/api'

export interface Application {
  id: string
  jobId: string
  candidateId: string
  recruiterId: string
  status: 'pending' | 'reviewed' | 'interviewed' | 'offered' | 'hired' | 'rejected'
  coverLetter?: string
  resumeUrl: string
  appliedAt: string
  updatedAt: string
  job: {
    id: string
    title: string
    company: string
    location: string
  }
  candidate: {
    id: string
    name: string
    email: string
  }
}

export interface CreateApplicationData {
  jobId: string
  coverLetter?: string
  resumeUrl: string
}

export interface ApplicationFilters {
  status?: string
  jobId?: string
  candidateId?: string
  recruiterId?: string
}

export const applicationService = {
  getApplications: async (filters?: ApplicationFilters, page = 1, limit = 10): Promise<{ applications: Application[]; total: number }> => {
    const response = await api.get('/applications', {
      params: { ...filters, page, limit }
    })
    return response.data
  },

  getApplicationById: async (id: string): Promise<Application> => {
    const response = await api.get(`/applications/${id}`)
    return response.data
  },

  createApplication: async (data: CreateApplicationData): Promise<Application> => {
    const response = await api.post('/applications', data)
    return response.data
  },

  updateApplicationStatus: async (id: string, status: Application['status']): Promise<Application> => {
    const response = await api.patch(`/applications/${id}/status`, { status })
    return response.data
  },

  withdrawApplication: async (id: string): Promise<void> => {
    await api.post(`/applications/${id}/withdraw`)
  },

  getCandidateApplications: async (candidateId: string): Promise<Application[]> => {
    const response = await api.get(`/applications/candidate/${candidateId}`)
    return response.data
  },

  getJobApplications: async (jobId: string): Promise<Application[]> => {
    const response = await api.get(`/applications/job/${jobId}`)
    return response.data
  },

  getRecruiterApplications: async (recruiterId: string): Promise<Application[]> => {
    const response = await api.get(`/applications/recruiter/${recruiterId}`)
    return response.data
  },
}
