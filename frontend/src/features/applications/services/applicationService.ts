import api from '@/lib/api';
import { Application, Job } from '@/types';

export interface ApplicationWithDetails extends Application {
  job_details?: Job;
  recruiter_notes?: string;
  timeline?: Array<{
    status: string;
    timestamp: string;
    note?: string;
    updated_by?: string;
  }>;
}

export interface ApplicationHistory {
  id: string;
  application: string;
  old_status: string;
  new_status: string;
  changed_at: string;
  changed_by?: string;
  notes?: string;
}

export const applicationService = {
  // Get my applications
  getMyApplications: async (): Promise<ApplicationWithDetails[]> => {
    const response = await api.get('/applications/my/');
    return response.data;
  },

  // Get application details
  getApplication: async (id: string): Promise<ApplicationWithDetails> => {
    const response = await api.get(`/applications/${id}/`);
    return response.data;
  },

  // Update application status (withdraw)
  updateApplicationStatus: async (id: string, status: string): Promise<Application> => {
    const response = await api.patch(`/applications/${id}/status/`, { status });
    return response.data;
  },

  // Withdraw application
  withdrawApplication: async (id: string): Promise<Application> => {
    const response = await api.patch(`/applications/${id}/status/`, { status: 'withdrawn' });
    return response.data;
  },

  // Get application history
  getApplicationHistory: async (id: string): Promise<ApplicationHistory[]> => {
    const response = await api.get(`/applications/${id}/history/`);
    return response.data;
  },
};
