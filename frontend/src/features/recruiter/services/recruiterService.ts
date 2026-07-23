import api from '@/lib/api';

export interface RecruiterProfile {
  id: string;
  user: string;
  company?: string;
  title?: string;
  location?: string;
  company_website?: string;
  company_size?: string;
  industry?: string;
  company_description?: string;
  benefits?: string[];
  company_logo?: string;
  culture?: string;
  social_links?: {
    linkedin?: string;
    twitter?: string;
    facebook?: string;
  };
  hiring_preferences?: {
    experience_levels?: string[];
    employment_types?: string[];
    remote_friendly?: boolean;
  };
}

export interface RecruiterProfileUpdate {
  company?: string;
  title?: string;
  location?: string;
  company_website?: string;
  company_size?: string;
  industry?: string;
  company_description?: string;
  benefits?: string[];
  company_logo?: string;
  culture?: string;
  social_links?: {
    linkedin?: string;
    twitter?: string;
    facebook?: string;
  };
  hiring_preferences?: {
    experience_levels?: string[];
    employment_types?: string[];
    remote_friendly?: boolean;
  };
}

export interface DashboardStats {
  total_jobs: number;
  active_jobs: number;
  total_applications: number;
  pending_applications: number;
  shortlisted_candidates: number;
  scheduled_interviews: number;
  recent_applications: number;
  views_this_week: number;
}

export interface RecentActivity {
  id: string;
  type: 'application' | 'interview' | 'job' | 'candidate';
  title: string;
  description: string;
  timestamp: string;
  entity_id?: string;
}

export const recruiterService = {
  // Get recruiter profile
  getProfile: async (): Promise<RecruiterProfile> => {
    const response = await api.get('/profile/recruiter/');
    return response.data;
  },

  // Update recruiter profile
  updateProfile: async (data: RecruiterProfileUpdate): Promise<RecruiterProfile> => {
    const response = await api.patch('/profile/recruiter/', data);
    return response.data;
  },

  // Get dashboard stats
  getDashboardStats: async (): Promise<DashboardStats> => {
    const response = await api.get('/recruiter/dashboard/stats/');
    return response.data;
  },

  // Get recent activity
  getRecentActivity: async (): Promise<RecentActivity[]> => {
    const response = await api.get('/recruiter/dashboard/activity/');
    return response.data;
  },

  // Upload company logo
  uploadCompanyLogo: async (file: File): Promise<{ logo_url: string }> => {
    const formData = new FormData();
    formData.append('logo', file);
    const response = await api.post('/recruiter/company/logo/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};
