import api from '@/lib/api';
import { Job } from '@/types';

export interface JobSearchParams {
  query?: string;
  location?: string;
  employment_type?: string;
  experience_level?: string;
  remote?: boolean;
  salary_min?: number;
  salary_max?: number;
  skills?: string[];
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface JobSearchResponse {
  results: Job[];
  count: number;
  next: string | null;
  previous: string | null;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface JobApplyRequest {
  cover_letter?: string;
  resume_id?: string;
}

export const jobService = {
  // Get public jobs list
  getJobs: async (params?: JobSearchParams): Promise<JobSearchResponse> => {
    const response = await api.get('/jobs/', { params });
    return response.data;
  },

  // Get job details
  getJob: async (id: string): Promise<Job> => {
    const response = await api.get(`/jobs/${id}/`);
    return response.data;
  },

  // Apply to job
  applyToJob: async (jobId: string, data: JobApplyRequest): Promise<any> => {
    const response = await api.post(`/jobs/${jobId}/apply/`, data);
    return response.data;
  },

  // Get job match score
  getJobMatch: async (jobId: string): Promise<any> => {
    const response = await api.get(`/jobs/${jobId}/match/`);
    return response.data;
  },

  // Search jobs (advanced search using search engine)
  searchJobs: async (params: JobSearchParams): Promise<JobSearchResponse> => {
    const response = await api.get('/jobs/', { 
      params: {
        ...params,
        search: params.query,
      },
    });
    return response.data;
  },
};
