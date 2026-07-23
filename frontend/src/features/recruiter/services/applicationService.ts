import api from '@/lib/api';

export interface Application {
  id: string;
  job: string;
  candidate: string;
  resume_version: string;
  status: 'submitted' | 'under_review' | 'shortlisted' | 'rejected' | 'hired';
  created_at: string;
  updated_at: string;
  job_details?: {
    id: string;
    title: string;
    company_name: string;
    location: string;
  };
  candidate_details?: {
    id: string;
    email: string;
    first_name?: string;
    last_name?: string;
    candidate_profile?: {
      title?: string;
      skills?: string[];
      location?: string;
      experience_years?: number;
    };
  };
  resume_details?: {
    id: string;
    file_name: string;
    parsed_data?: any;
  };
  match_score?: number;
}

export interface ApplicationStatusUpdate {
  status: 'submitted' | 'under_review' | 'shortlisted' | 'rejected' | 'hired';
  notes?: string;
}

export interface ApplicationStatusHistory {
  id: string;
  application: string;
  old_status: string;
  new_status: string;
  changed_by: string;
  changed_by_name?: string;
  changed_at: string;
  notes?: string;
}

export interface ApplicationNote {
  id: string;
  application: string;
  content: string;
  created_by: string;
  created_by_name?: string;
  created_at: string;
  is_internal: boolean;
}

export const applicationService = {
  // Get applications for a job
  getJobApplications: async (jobId: string, status?: string): Promise<Application[]> => {
    const params = status ? { status } : {};
    const response = await api.get(`/jobs/${jobId}/applications/`, { params });
    return response.data;
  },

  // Get application details
  getApplication: async (id: string): Promise<Application> => {
    const response = await api.get(`/applications/${id}/`);
    return response.data;
  },

  // Update application status
  updateApplicationStatus: async (
    id: string,
    data: ApplicationStatusUpdate
  ): Promise<Application> => {
    const response = await api.patch(`/applications/${id}/status/`, data);
    return response.data;
  },

  // Get application history
  getApplicationHistory: async (id: string): Promise<ApplicationStatusHistory[]> => {
    const response = await api.get(`/applications/${id}/history/`);
    return response.data;
  },

  // Bulk update application status
  bulkUpdateStatus: async (
    applicationIds: string[],
    status: 'submitted' | 'under_review' | 'shortlisted' | 'rejected' | 'hired'
  ): Promise<Application[]> => {
    const promises = applicationIds.map(id =>
      applicationService.updateApplicationStatus(id, { status })
    );
    return await Promise.all(promises);
  },

  // Shortlist candidate
  shortlistCandidate: async (applicationId: string): Promise<Application> => {
    return await applicationService.updateApplicationStatus(applicationId, {
      status: 'shortlisted',
    });
  },

  // Reject candidate
  rejectCandidate: async (applicationId: string, notes?: string): Promise<Application> => {
    return await applicationService.updateApplicationStatus(applicationId, {
      status: 'rejected',
      notes,
    });
  },

  // Hire candidate
  hireCandidate: async (applicationId: string): Promise<Application> => {
    return await applicationService.updateApplicationStatus(applicationId, {
      status: 'hired',
    });
  },

  // Add note to application
  addNote: async (
    applicationId: string,
    content: string,
    isInternal: boolean = true
  ): Promise<ApplicationNote> => {
    const response = await api.post(`/applications/${applicationId}/notes/`, {
      content,
      is_internal: isInternal,
    });
    return response.data;
  },

  // Get application notes
  getNotes: async (applicationId: string): Promise<ApplicationNote[]> => {
    const response = await api.get(`/applications/${applicationId}/notes/`);
    return response.data;
  },
};
