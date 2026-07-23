import api from '@/lib/api';
import { AnalyticsData } from '@/types';

export interface CandidateDashboardData extends AnalyticsData {
  recent_activity?: Array<{
    type: string;
    description: string;
    timestamp: string;
  }>;
  upcoming_interviews?: number;
  saved_jobs?: number;
  profile_views?: number;
  search_appearance?: number;
}

export const analyticsService = {
  // Get candidate dashboard analytics
  getCandidateDashboard: async (): Promise<CandidateDashboardData> => {
    const response = await api.get('/analytics/candidate/dashboard/');
    return response.data;
  },
};
