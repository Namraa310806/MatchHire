import api from '@/lib/api';

export interface Interview {
  id: string;
  application: string;
  scheduled_at: string;
  duration_minutes?: number;
  interview_type: 'phone' | 'video' | 'onsite';
  status: 'scheduled' | 'completed' | 'cancelled';
  meeting_link?: string;
  location?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  application_details?: {
    id: string;
    candidate: string;
    candidate_name?: string;
    job: string;
    job_title?: string;
  };
}

export interface InterviewCreate {
  application: string;
  scheduled_at: string;
  duration_minutes?: number;
  interview_type: 'phone' | 'video' | 'onsite';
  meeting_link?: string;
  location?: string;
  notes?: string;
}

export interface InterviewUpdate {
  scheduled_at?: string;
  duration_minutes?: number;
  interview_type?: 'phone' | 'video' | 'onsite';
  meeting_link?: string;
  location?: string;
  notes?: string;
  status?: 'scheduled' | 'completed' | 'cancelled';
}

export const interviewService = {
  // Create interview
  createInterview: async (data: InterviewCreate): Promise<Interview> => {
    const response = await api.post('/interviews/', data);
    return response.data;
  },

  // Get interview details
  getInterview: async (id: string): Promise<Interview> => {
    const response = await api.get(`/interviews/${id}/`);
    return response.data;
  },

  // Update interview
  updateInterview: async (id: string, data: InterviewUpdate): Promise<Interview> => {
    const response = await api.patch(`/interviews/${id}/`, data);
    return response.data;
  },

  // Cancel interview
  cancelInterview: async (id: string): Promise<Interview> => {
    return await interviewService.updateInterview(id, { status: 'cancelled' });
  },

  // Complete interview
  completeInterview: async (id: string, notes?: string): Promise<Interview> => {
    return await interviewService.updateInterview(id, {
      status: 'completed',
      notes,
    });
  },

  // Reschedule interview
  rescheduleInterview: async (id: string, scheduledAt: string): Promise<Interview> => {
    return await interviewService.updateInterview(id, { scheduled_at: scheduledAt });
  },

  // Get upcoming interviews
  getUpcomingInterviews: async (): Promise<Interview[]> => {
    const response = await api.get('/interviews/upcoming/');
    return response.data;
  },

  // Get past interviews
  getPastInterviews: async (): Promise<Interview[]> => {
    const response = await api.get('/interviews/past/');
    return response.data;
  },

  // Get interviews for a job
  getJobInterviews: async (jobId: string): Promise<Interview[]> => {
    const response = await api.get(`/jobs/${jobId}/interviews/`);
    return response.data;
  },

  // Add interview feedback
  addFeedback: async (interviewId: string, feedback: string): Promise<Interview> => {
    return await interviewService.updateInterview(interviewId, { notes: feedback });
  },
};
