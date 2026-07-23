export interface User {
  id: string;
  email: string;
  role: 'candidate' | 'recruiter' | 'admin';
  first_name?: string;
  last_name?: string;
  is_verified?: boolean;
}

export interface Candidate extends User {
  role: 'candidate';
  candidate_profile?: {
    id: string;
    title?: string;
    experience_years?: number;
    skills?: string[];
    location?: string;
    resume_url?: string;
  };
}

export interface Recruiter extends User {
  role: 'recruiter';
  recruiter_profile?: {
    id: string;
    company?: string;
    title?: string;
    location?: string;
  };
}

export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  description: string;
  requirements?: string;
  salary_min?: number;
  salary_max?: number;
  employment_type: 'full-time' | 'part-time' | 'contract' | 'internship';
  experience_level: 'entry' | 'mid' | 'senior' | 'executive';
  remote: boolean;
  posted_at: string;
  is_active: boolean;
  skills?: string[];
}

export interface Application {
  id: string;
  job: Job;
  candidate: Candidate;
  status: 'pending' | 'reviewed' | 'interview' | 'offered' | 'rejected' | 'withdrawn';
  applied_at: string;
  cover_letter?: string;
}

export interface Resume {
  id: string;
  file_name: string;
  uploaded_at: string;
  is_active: boolean;
  parsed_data?: any;
}

export interface Interview {
  id: string;
  application: Application;
  scheduled_at: string;
  status: 'scheduled' | 'completed' | 'cancelled';
  interview_type: 'phone' | 'video' | 'onsite';
  notes?: string;
}

export interface Recommendation {
  id: string;
  entity_id: string;
  score: number;
  explanation?: string;
  signals?: Record<string, number>;
}

export interface AnalyticsData {
  total_applications: number;
  total_views: number;
  total_interviews: number;
  application_rate: number;
  interview_rate: number;
  skills?: Record<string, number>;
  timeline?: Array<{ date: string; count: number }>;
}
