import api from '@/lib/api';
import { Candidate } from '@/types';

export interface CandidateProfile {
  id: string;
  user: string;
  title?: string;
  experience_years?: number;
  skills?: string[];
  location?: string;
  resume_url?: string;
  phone?: string;
  linkedin_url?: string;
  github_url?: string;
  portfolio_url?: string;
  education?: Array<{
    institution: string;
    degree: string;
    field_of_study: string;
    start_date: string;
    end_date?: string;
  }>;
  experience?: Array<{
    company: string;
    position: string;
    start_date: string;
    end_date?: string;
    description?: string;
  }>;
  certifications?: Array<{
    name: string;
    issuer: string;
    date: string;
    credential_url?: string;
  }>;
  languages?: Array<{
    language: string;
    proficiency: string;
  }>;
  professional_summary?: string;
  profile_completion?: number;
}

export interface CandidateProfileUpdate {
  title?: string;
  experience_years?: number;
  skills?: string[];
  location?: string;
  phone?: string;
  linkedin_url?: string;
  github_url?: string;
  portfolio_url?: string;
  education?: Array<{
    institution: string;
    degree: string;
    field_of_study: string;
    start_date: string;
    end_date?: string;
  }>;
  experience?: Array<{
    company: string;
    position: string;
    start_date: string;
    end_date?: string;
    description?: string;
  }>;
  certifications?: Array<{
    name: string;
    issuer: string;
    date: string;
    credential_url?: string;
  }>;
  languages?: Array<{
    language: string;
    proficiency: string;
  }>;
  professional_summary?: string;
}

export const candidateService = {
  // Get current candidate profile
  getProfile: async (): Promise<CandidateProfile> => {
    const response = await api.get('/profile/candidate/');
    return response.data;
  },

  // Update candidate profile
  updateProfile: async (data: CandidateProfileUpdate): Promise<CandidateProfile> => {
    const response = await api.patch('/profile/candidate/', data);
    return response.data;
  },

  // Get current user info
  getCurrentUser: async (): Promise<Candidate> => {
    const response = await api.get('/profile/');
    return response.data;
  },

  // Update user info
  updateUser: async (data: {
    first_name?: string;
    last_name?: string;
    email?: string;
  }): Promise<Candidate> => {
    const response = await api.patch('/profile/', data);
    return response.data;
  },

  // Calculate profile completion
  calculateProfileCompletion: (profile: CandidateProfile): number => {
    const fields = [
      profile.title,
      profile.experience_years,
      profile.skills?.length,
      profile.location,
      profile.phone,
      profile.professional_summary,
      profile.education?.length,
      profile.experience?.length,
    ];
    
    const completedFields = fields.filter(field => 
      field !== undefined && field !== null && field !== '' && 
      (typeof field === 'number' ? field > 0 : true)
    ).length;
    
    return Math.round((completedFields / fields.length) * 100);
  },
};
