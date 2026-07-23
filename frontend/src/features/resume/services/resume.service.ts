import api from '@/lib/api'

export interface Resume {
  id: string
  candidateId: string
  firstName: string
  lastName: string
  email: string
  phone: string
  location: string
  summary: string
  experience: Experience[]
  education: Education[]
  skills: string[]
  languages: Language[]
  certifications: Certification[]
  fileUrl?: string
  createdAt: string
  updatedAt: string
}

export interface Experience {
  id?: string
  company: string
  position: string
  startDate: string
  endDate?: string
  current: boolean
  description: string
}

export interface Education {
  id?: string
  institution: string
  degree: string
  field: string
  startDate: string
  endDate?: string
  current: boolean
  gpa?: string
}

export interface Language {
  language: string
  proficiency: 'basic' | 'intermediate' | 'advanced' | 'native'
}

export interface Certification {
  name: string
  issuer: string
  date: string
  url?: string
}

export const resumeService = {
  getResume: async (candidateId: string): Promise<Resume> => {
    const response = await api.get(`/resume/${candidateId}`)
    return response.data
  },

  createResume: async (data: Partial<Resume>): Promise<Resume> => {
    const response = await api.post('/resume', data)
    return response.data
  },

  updateResume: async (candidateId: string, data: Partial<Resume>): Promise<Resume> => {
    const response = await api.put(`/resume/${candidateId}`, data)
    return response.data
  },

  uploadResumeFile: async (file: File): Promise<{ fileUrl: string }> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/resume/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  parseResume: async (file: File): Promise<Partial<Resume>> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/resume/parse', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  deleteResume: async (candidateId: string): Promise<void> => {
    await api.delete(`/resume/${candidateId}`)
  },
}
