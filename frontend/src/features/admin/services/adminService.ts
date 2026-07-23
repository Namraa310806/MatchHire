import axios from 'axios';
import type {
  AdminDashboardStats,
  AdminUser,
  AdminUserUpdate,
  AdminJob,
  AdminJobUpdate,
  AdminCompany,
  AdminCompanyUpdate,
  AdminResume,
  AdminResumeUpdate,
  AdminApplication,
  PaginatedResponse,
  UserListParams,
  JobListParams,
  CompanyListParams,
  ResumeListParams,
  ApplicationListParams,
  HealthStatus,
  SearchMetrics,
  RecommendationMetrics,
  SystemMetrics,
  FeatureFlag,
  AuditLog,
  AuditLogFilters,
  SecurityEvent,
  LoginActivity,
  SystemConfig,
} from '../types';

const API_BASE = '/api/admin';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Dashboard
export const adminApi = {
  // Dashboard
  getDashboardStats: async (): Promise<AdminDashboardStats> => {
    const { data } = await api.get<AdminDashboardStats>('/dashboard/');
    return data;
  },

  // Users
  getUsers: async (params: UserListParams): Promise<PaginatedResponse<AdminUser>> => {
    const { data } = await api.get<PaginatedResponse<AdminUser>>('/users/', { params });
    return data;
  },

  getUser: async (id: string): Promise<AdminUser> => {
    const { data } = await api.get<AdminUser>(`/users/${id}/`);
    return data;
  },

  updateUser: async (id: string, update: AdminUserUpdate): Promise<AdminUser> => {
    const { data } = await api.patch<AdminUser>(`/users/${id}/`, update);
    return data;
  },

  // Jobs
  getJobs: async (params: JobListParams): Promise<PaginatedResponse<AdminJob>> => {
    const { data } = await api.get<PaginatedResponse<AdminJob>>('/jobs/', { params });
    return data;
  },

  updateJob: async (id: string, update: AdminJobUpdate): Promise<AdminJob> => {
    const { data } = await api.patch<AdminJob>(`/jobs/${id}/`, update);
    return data;
  },

  // Resumes
  getResumes: async (params: ResumeListParams): Promise<PaginatedResponse<AdminResume>> => {
    const { data } = await api.get<PaginatedResponse<AdminResume>>('/resumes/', { params });
    return data;
  },

  updateResume: async (id: string, update: AdminResumeUpdate): Promise<AdminResume> => {
    const { data } = await api.patch<AdminResume>(`/resumes/${id}/`, update);
    return data;
  },

  // Applications
  getApplications: async (params: ApplicationListParams): Promise<PaginatedResponse<AdminApplication>> => {
    const { data } = await api.get<PaginatedResponse<AdminApplication>>('/applications/', { params });
    return data;
  },

  // Companies
  getCompanies: async (params: CompanyListParams): Promise<PaginatedResponse<AdminCompany>> => {
    const { data } = await api.get<PaginatedResponse<AdminCompany>>('/companies/', { params });
    return data;
  },

  updateCompany: async (id: string, update: AdminCompanyUpdate): Promise<AdminCompany> => {
    const { data } = await api.patch<AdminCompany>(`/companies/${id}/`, update);
    return data;
  },
};

// Health & Observability
export const healthApi = {
  getHealthStatus: async (): Promise<HealthStatus> => {
    const { data } = await axios.get<HealthStatus>('/api/health/');
    return data;
  },

  getReadiness: async (): Promise<{ ready: boolean; message: string; uptime_seconds: number }> => {
    const { data } = await axios.get('/api/ready/');
    return data;
  },

  getLiveness: async (): Promise<{ alive: boolean; message: string; timestamp: string }> => {
    const { data } = await axios.get('/api/live/');
    return data;
  },
};

// Search Metrics (mock - would be real endpoint if available)
export const searchMetricsApi = {
  getSearchMetrics: async (): Promise<SearchMetrics> => {
    // This would be a real endpoint if backend exposes search metrics
    // For now, return mock data
    return {
      provider: 'postgresql',
      index_status: 'healthy',
      document_count: 0,
      query_latency_p50: 50,
      query_latency_p95: 120,
      query_latency_p99: 200,
      index_latency_p50: 100,
      cache_hit_ratio: 0.85,
      top_queries: [],
      search_failures: 0,
      total_queries: 0,
    };
  },
};

// Recommendation Metrics (mock - would be real endpoint if available)
export const recommendationMetricsApi = {
  getRecommendationMetrics: async (): Promise<RecommendationMetrics> => {
    // This would be a real endpoint if backend exposes recommendation metrics
    return {
      total_requests: 0,
      acceptance_rate: 0,
      avg_confidence: 0,
      latency_p50: 100,
      latency_p95: 250,
      feedback_count: 0,
      positive_feedback: 0,
      negative_feedback: 0,
    };
  },
};

// System Metrics (mock - would be real endpoint if available)
export const systemMetricsApi = {
  getSystemMetrics: async (): Promise<SystemMetrics> => {
    // This would be a real endpoint if backend exposes system metrics
    return {
      api_latency_p50: 100,
      api_latency_p95: 300,
      api_latency_p99: 500,
      request_volume: 0,
      error_rate: 0,
      cache_hit_ratio: 0.85,
      queue_status: [],
      background_jobs: [],
      service_health: [],
    };
  },
};

// Feature Flags (mock - UI only for now)
export const featureFlagsApi = {
  getFeatureFlags: async (): Promise<FeatureFlag[]> => {
    // This would be a real endpoint if backend supports feature flags
    return [];
  },

  updateFeatureFlag: async (_id: string, _enabled: boolean): Promise<FeatureFlag> => {
    // This would be a real endpoint if backend supports feature flags
    throw new Error('Feature flag management not implemented in backend');
  },
};

// Audit Logs (mock - UI only for now)
export const auditLogsApi = {
  getAuditLogs: async (_filters: AuditLogFilters): Promise<PaginatedResponse<AuditLog>> => {
    // This would be a real endpoint if backend supports audit logs
    return {
      count: 0,
      next: null,
      previous: null,
      results: [],
    };
  },
};

// Security Events (mock - UI only for now)
export const securityApi = {
  getSecurityEvents: async (): Promise<SecurityEvent[]> => {
    // This would be a real endpoint if backend supports security events
    return [];
  },

  getLoginActivity: async (): Promise<LoginActivity[]> => {
    // This would be a real endpoint if backend supports login activity
    return [];
  },
};

// System Configuration (read-only mock)
export const systemConfigApi = {
  getSystemConfig: async (): Promise<SystemConfig> => {
    // This would be a real endpoint if backend exposes system config
    return {
      general: {
        site_name: 'MatchHire',
        site_url: '',
        support_email: 'support@matchhire.com',
        max_upload_size_mb: 10,
        allowed_file_types: ['.pdf', '.doc', '.docx'],
      },
      email: {
        provider: 'smtp',
        from_email: 'noreply@matchhire.com',
        from_name: 'MatchHire',
        smtp_host: 'localhost',
        smtp_port: 587,
        use_tls: true,
        api_key: '',
      },
      storage: {
        provider: 'local',
        bucket_name: '',
        region: '',
        cdn_url: null,
      },
      search: {
        provider: 'postgresql',
        index_name: 'matchhire',
        min_score: 0.5,
        fuzziness: 1,
      },
      recommendation: {
        enabled: true,
        strategy: 'hybrid',
        min_match_score: 0.5,
        max_results: 20,
      },
      analytics: {
        enabled: true,
        provider: 'internal',
        tracking_id: null,
        sample_rate: 1.0,
      },
      maintenance: {
        maintenance_mode: false,
        maintenance_message: '',
        scheduled_maintenance: null,
      },
      environment: {
        name: 'development',
        version: '1.0.0',
        deploy_time: new Date().toISOString(),
        git_commit: '',
      },
    };
  },
};
