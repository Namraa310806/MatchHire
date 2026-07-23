import api from '@/lib/api'

export interface Job {
  id: string
  title: string
  description: string
  requirements: string[]
  responsibilities: string[]
  location: string
  salary: {
    min: number
    max: number
    currency: string
  }
  employmentType: 'full-time' | 'part-time' | 'contract' | 'internship'
  experienceLevel: 'entry' | 'mid' | 'senior' | 'executive'
  skills: string[]
  companyId: string
  companyName: string
  status: 'active' | 'closed' | 'draft'
  createdAt: string
  updatedAt: string
}

export interface CreateJobData {
  title: string
  description: string
  requirements: string[]
  responsibilities: string[]
  location: string
  salary: {
    min: number
    max: number
    currency: string
  }
  employmentType: 'full-time' | 'part-time' | 'contract' | 'internship'
  experienceLevel: 'entry' | 'mid' | 'senior' | 'executive'
  skills: string[]
}

export interface JobFilters {
  search?: string
  location?: string
  employmentType?: string
  experienceLevel?: string
  skills?: string[]
  salaryMin?: number
  salaryMax?: number
}

export const jobService = {
  getJobs: async (filters?: JobFilters, page = 1, limit = 10): Promise<{ jobs: Job[]; total: number }> => {
    const response = await api.get('/jobs', {
      params: { ...filters, page, limit }
    })
    return response.data
  },

  getJobById: async (id: string): Promise<Job> => {
    const response = await api.get(`/jobs/${id}`)
    return response.data
  },

  createJob: async (data: CreateJobData): Promise<Job> => {
    const response = await api.post('/jobs', data)
    return response.data
  },

  updateJob: async (id: string, data: Partial<CreateJobData>): Promise<Job> => {
    const response = await api.put(`/jobs/${id}`, data)
    return response.data
  },

  deleteJob: async (id: string): Promise<void> => {
    await api.delete(`/jobs/${id}`)
  },

  getRecommendedJobs: async (candidateId: string): Promise<Job[]> => {
    const response = await api.get(`/jobs/recommendations/${candidateId}`)
    return response.data
  },

  getCompanyJobs: async (companyId: string): Promise<Job[]> => {
    const response = await api.get(`/jobs/company/${companyId}`)
    return response.data
  },
}
