import api from '@/lib/api';

export interface Job {
  id: string;
  recruiter: string;
  title: string;
  company_name: string;
  location: string;
  employment_type: 'full_time' | 'part_time' | 'contract' | 'internship';
  experience_level: 'entry' | 'junior' | 'mid' | 'senior' | 'lead';
  description: string;
  requirements?: string;
  responsibilities?: string;
  salary_min?: number;
  salary_max?: number;
  currency: string;
  is_remote: boolean;
  status: 'draft' | 'active' | 'closed';
  created_at: string;
  updated_at: string;
  closed_at?: string;
  skills?: string[];
}

export interface JobCreate {
  title: string;
  company_name: string;
  location: string;
  employment_type: 'full_time' | 'part_time' | 'contract' | 'internship';
  experience_level: 'entry' | 'junior' | 'mid' | 'senior' | 'lead';
  description: string;
  requirements?: string;
  responsibilities?: string;
  salary_min?: number;
  salary_max?: number;
  currency?: string;
  is_remote?: boolean;
  status?: 'draft' | 'active';
  skills?: string[];
}

export interface JobUpdate {
  title?: string;
  company_name?: string;
  location?: string;
  employment_type?: 'full_time' | 'part_time' | 'contract' | 'internship';
  experience_level?: 'entry' | 'junior' | 'mid' | 'senior' | 'lead';
  description?: string;
  requirements?: string;
  responsibilities?: string;
  salary_min?: number;
  salary_max?: number;
  currency?: string;
  is_remote?: boolean;
  status?: 'draft' | 'active' | 'closed';
  skills?: string[];
}

export interface JobSearchParams {
  q?: string;
  location?: string;
  employment_type?: string;
  experience_level?: string;
  is_remote?: boolean;
  salary_min?: number;
  salary_max?: number;
  ordering?: string;
  page?: number;
  page_size?: number;
}

export interface PaginatedJobs {
  count: number;
  next: string | null;
  previous: string | null;
  results: Job[];
}

export const jobService = {
  // Create job
  createJob: async (data: JobCreate): Promise<Job> => {
    const response = await api.post('/jobs/', data);
    return response.data;
  },

  // Get my jobs (recruiter's jobs)
  getMyJobs: async (): Promise<Job[]> => {
    const response = await api.get('/jobs/my/');
    return response.data;
  },

  // Get job details
  getJob: async (id: string): Promise<Job> => {
    const response = await api.get(`/jobs/${id}/`);
    return response.data;
  },

  // Update job
  updateJob: async (id: string, data: JobUpdate): Promise<Job> => {
    const response = await api.patch(`/jobs/${id}/`, data);
    return response.data;
  },

  // Close job
  closeJob: async (id: string): Promise<Job> => {
    const response = await api.post(`/jobs/${id}/close/`);
    return response.data;
  },

  // Delete job
  deleteJob: async (id: string): Promise<void> => {
    await api.delete(`/jobs/${id}/`);
  },

  // Duplicate job
  duplicateJob: async (id: string): Promise<Job> => {
    const job = await jobService.getJob(id);
    const { id: _, created_at, updated_at, closed_at, ...jobData } = job;
    return await jobService.createJob({
      ...jobData,
      title: `${jobData.title} (Copy)`,
      status: 'draft',
    });
  },

  // Search jobs (public)
  searchJobs: async (params: JobSearchParams): Promise<PaginatedJobs> => {
    const response = await api.get('/jobs/', { params });
    return response.data;
  },

  // Publish job (change status to active)
  publishJob: async (id: string): Promise<Job> => {
    return await jobService.updateJob(id, { status: 'active' });
  },

  // Archive job (change status to closed)
  archiveJob: async (id: string): Promise<Job> => {
    return await jobService.closeJob(id);
  },
};
