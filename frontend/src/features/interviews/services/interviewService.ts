import api from '@/lib/api';
import { Interview } from '@/types';

export interface InterviewWithDetails extends Interview {
  application_details?: {
    job: any;
    candidate: any;
  };
  recruiter_name?: string;
  recruiter_email?: string;
  meeting_link?: string;
  preparation_notes?: string;
}

export interface InterviewHistory {
  id: string;
  interview: string;
  old_status: string;
  new_status: string;
  changed_at: string;
  changed_by?: string;
  notes?: string;
}

export const interviewService = {
  // Get interviews for an application
  getApplicationInterviews: async (applicationId: string): Promise<InterviewWithDetails[]> => {
    const response = await api.get(`/interviews/applications/${applicationId}/interviews/`);
    return response.data;
  },

  // Get my interviews (for current candidate)
  getMyInterviews: async (): Promise<InterviewWithDetails[]> => {
    const response = await api.get(`/interviews/my-interviews/`);
    return response.data;
  },

  // Get interview details
  getInterview: async (interviewId: string): Promise<InterviewWithDetails> => {
    const response = await api.get(`/interviews/interviews/${interviewId}/`);
    return response.data;
  },

  // Update interview status
  updateInterviewStatus: async (interviewId: string, status: string): Promise<Interview> => {
    const response = await api.patch(`/interviews/interviews/${interviewId}/status/`, { status });
    return response.data;
  },

  // Get interview history
  getInterviewHistory: async (interviewId: string): Promise<InterviewHistory[]> => {
    const response = await api.get(`/interviews/interviews/${interviewId}/history/`);
    return response.data;
  },
};
