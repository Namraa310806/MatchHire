import api from '@/lib/api';

export interface HiringFunnel {
  stage: string;
  count: number;
  percentage: number;
}

export interface TimeToHire {
  average_days: number;
  median_days: number;
  by_job: Array<{
    job_id: string;
    job_title: string;
    days: number;
  }>;
}

export interface ApplicationTrend {
  date: string;
  count: number;
}

export interface JobPerformance {
  job_id: string;
  job_title: string;
  views: number;
  applications: number;
  interviews: number;
  offers: number;
  conversion_rate: number;
  time_to_hire?: number;
}

export interface SearchPerformance {
  search_term: string;
  result_count: number;
  click_rate: number;
  conversion_rate: number;
}

export interface RecommendationEffectiveness {
  total_recommendations: number;
  accepted: number;
  rejected: number;
  acceptance_rate: number;
  average_match_score: number;
}

export interface InterviewConversion {
  total_interviews: number;
  scheduled: number;
  completed: number;
  hired: number;
  completion_rate: number;
  hire_rate: number;
}

export interface RecruiterActivity {
  date: string;
  jobs_posted: number;
  applications_reviewed: number;
  interviews_scheduled: number;
  messages_sent: number;
}

export interface PipelineAnalytics {
  funnel: HiringFunnel[];
  time_to_hire: TimeToHire;
  application_trends: ApplicationTrend[];
  job_performance: JobPerformance[];
  interview_conversion: InterviewConversion;
}

export const analyticsService = {
  // Get hiring funnel
  getHiringFunnel: async (jobId?: string): Promise<HiringFunnel[]> => {
    const params = jobId ? { job_id: jobId } : {};
    const response = await api.get('/analytics/funnel/', { params });
    return response.data;
  },

  // Get time to hire
  getTimeToHire: async (jobId?: string): Promise<TimeToHire> => {
    const params = jobId ? { job_id: jobId } : {};
    const response = await api.get('/analytics/time-to-hire/', { params });
    return response.data;
  },

  // Get application trends
  getApplicationTrends: async (
    days: number = 30
  ): Promise<ApplicationTrend[]> => {
    const response = await api.get('/analytics/application-trends/', {
      params: { days },
    });
    return response.data;
  },

  // Get job performance
  getJobPerformance: async (): Promise<JobPerformance[]> => {
    const response = await api.get('/analytics/job-performance/');
    return response.data;
  },

  // Get search performance
  getSearchPerformance: async (): Promise<SearchPerformance[]> => {
    const response = await api.get('/analytics/search-performance/');
    return response.data;
  },

  // Get recommendation effectiveness
  getRecommendationEffectiveness: async (): Promise<RecommendationEffectiveness> => {
    const response = await api.get('/analytics/recommendation-effectiveness/');
    return response.data;
  },

  // Get interview conversion
  getInterviewConversion: async (jobId?: string): Promise<InterviewConversion> => {
    const params = jobId ? { job_id: jobId } : {};
    const response = await api.get('/analytics/interview-conversion/', { params });
    return response.data;
  },

  // Get recruiter activity
  getRecruiterActivity: async (days: number = 30): Promise<RecruiterActivity[]> => {
    const response = await api.get('/analytics/recruiter-activity/', {
      params: { days },
    });
    return response.data;
  },

  // Get pipeline analytics (combined)
  getPipelineAnalytics: async (jobId?: string): Promise<PipelineAnalytics> => {
    const params = jobId ? { job_id: jobId } : {};
    const response = await api.get('/analytics/pipeline/', { params });
    return response.data;
  },

  // Get offer conversion
  getOfferConversion: async (): Promise<{
    total_offers: number;
    accepted: number;
    rejected: number;
    acceptance_rate: number;
  }> => {
    const response = await api.get('/analytics/offer-conversion/');
    return response.data;
  },
};
