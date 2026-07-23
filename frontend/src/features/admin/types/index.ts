// Admin Types

export interface AdminDashboardStats {
  total_users: number;
  total_jobs: number;
  total_applications: number;
  total_companies: number;
  active_users: number;
  active_jobs: number;
  pending_jobs: number;
  closed_jobs: number;
  total_interviews: number;
  total_matches: number;
}

export interface AdminUser {
  id: string;
  email: string;
  full_name: string | null;
  role: 'candidate' | 'recruiter' | 'admin';
  is_active: boolean;
  date_joined: string;
  last_login: string | null;
  profile_complete: boolean;
}

export interface AdminUserUpdate {
  is_active?: boolean;
  role?: 'candidate' | 'recruiter' | 'admin';
  reason?: string;
}

export interface AdminJob {
  id: string;
  title: string;
  company_name: string;
  status: 'draft' | 'active' | 'closed' | 'archived';
  created_at: string;
  recruiter_id: string;
  recruiter_email: string;
  location: string | null;
  employment_type: string | null;
  applications_count: number;
}

export interface AdminJobUpdate {
  status?: 'draft' | 'active' | 'closed' | 'archived';
  reason?: string;
}

export interface AdminCompany {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  website: string | null;
  logo_url: string | null;
  industry: string | null;
  company_size: string | null;
  location: string | null;
  status: 'pending' | 'approved' | 'rejected' | 'suspended';
  created_at: string;
  updated_at: string;
  recruiter_count: number;
  job_count: number;
}

export interface AdminCompanyUpdate {
  status?: 'pending' | 'approved' | 'rejected' | 'suspended';
  reason?: string;
}

export interface CompanyListParams extends ListParams {
  status?: string;
  industry?: string;
}

export interface AdminResume {
  id: string;
  user_id: string;
  user_email: string;
  user_name: string | null;
  created_at: string;
  is_parsed: boolean;
  has_structured_data: boolean;
  current_version_id: string | null;
  file_name: string | null;
  file_size: number;
}

export interface AdminResumeUpdate {
  is_active?: boolean;
  reason?: string;
}

export interface AdminApplication {
  id: string;
  status: 'submitted' | 'under_review' | 'shortlisted' | 'rejected' | 'hired';
  created_at: string;
  updated_at: string;
  candidate_id: string;
  candidate_name: string | null;
  candidate_email: string;
  job_id: string;
  job_title: string;
  company_name: string;
  recruiter_id: string;
  recruiter_email: string;
  resume_version_id: string | null;
  cover_letter: string | null;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ListParams {
  page?: number;
  page_size?: number;
  ordering?: string;
  search?: string;
}

export interface UserListParams extends ListParams {
  role?: string;
  is_active?: boolean;
}

export interface JobListParams extends ListParams {
  status?: string;
  company?: string;
  recruiter_id?: string;
}

export interface ResumeListParams extends ListParams {
  candidate_id?: string;
  parsed?: boolean;
  structured?: boolean;
}

export interface ApplicationListParams extends ListParams {
  status?: string;
  candidate_id?: string;
  job_id?: string;
  recruiter_id?: string;
}

// Health & Observability Types
export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  checks: HealthCheck[];
}

export interface HealthCheck {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  message: string;
  duration_ms: number;
  metadata: Record<string, any>;
}

export interface SearchMetrics {
  provider: string;
  index_status: string;
  document_count: number;
  query_latency_p50: number;
  query_latency_p95: number;
  query_latency_p99: number;
  index_latency_p50: number;
  cache_hit_ratio: number;
  top_queries: QueryStat[];
  search_failures: number;
  total_queries: number;
}

export interface QueryStat {
  query: string;
  count: number;
  avg_latency_ms: number;
}

export interface RecommendationMetrics {
  total_requests: number;
  acceptance_rate: number;
  avg_confidence: number;
  latency_p50: number;
  latency_p95: number;
  feedback_count: number;
  positive_feedback: number;
  negative_feedback: number;
}

export interface SystemMetrics {
  api_latency_p50: number;
  api_latency_p95: number;
  api_latency_p99: number;
  request_volume: number;
  error_rate: number;
  cache_hit_ratio: number;
  queue_status: QueueStatus[];
  background_jobs: JobStatus[];
  service_health: ServiceHealth[];
}

export interface QueueStatus {
  name: string;
  size: number;
  processing: number;
  failed: number;
}

export interface JobStatus {
  name: string;
  status: 'running' | 'idle' | 'failed';
  last_run: string | null;
  next_run: string | null;
}

export interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  uptime: number;
  last_check: string;
}

// Feature Flags
export interface FeatureFlag {
  id: string;
  key: string;
  name: string;
  description: string;
  enabled: boolean;
  environment: 'development' | 'staging' | 'production';
  created_at: string;
  updated_at: string;
  audit_history: AuditEntry[];
}

export interface AuditEntry {
  id: string;
  action: string;
  performed_by: string;
  performed_at: string;
  changes: Record<string, any>;
}

// Audit Logs
export interface AuditLog {
  id: string;
  timestamp: string;
  actor: string;
  actor_type: 'user' | 'system' | 'admin';
  action: string;
  resource_type: string;
  resource_id: string | null;
  details: Record<string, any>;
  ip_address: string | null;
  user_agent: string | null;
}

export interface AuditLogFilters {
  action?: string;
  actor?: string;
  resource_type?: string;
  start_date?: string;
  end_date?: string;
}

// Security
export interface SecurityEvent {
  id: string;
  timestamp: string;
  event_type: 'login_success' | 'login_failure' | 'account_locked' | 'permission_changed' | 'role_changed';
  user_id: string | null;
  user_email: string | null;
  ip_address: string;
  user_agent: string | null;
  details: Record<string, any>;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface LoginActivity {
  user_id: string;
  user_email: string;
  last_login: string;
  login_count: number;
  failed_attempts: number;
  last_failed_login: string | null;
  current_session_ip: string | null;
}

// System Configuration
export interface SystemConfig {
  general: GeneralConfig;
  email: EmailConfig;
  storage: StorageConfig;
  search: SearchConfig;
  recommendation: RecommendationConfig;
  analytics: AnalyticsConfig;
  maintenance: MaintenanceConfig;
  environment: EnvironmentInfo;
}

export interface GeneralConfig {
  site_name: string;
  site_url: string;
  support_email: string;
  max_upload_size_mb: number;
  allowed_file_types: string[];
}

export interface EmailConfig {
  provider: string;
  from_email: string;
  from_name: string;
  smtp_host: string;
  smtp_port: number;
  use_tls: boolean;
  api_key: string;
}

export interface StorageConfig {
  provider: 'local' | 's3' | 'azure' | 'gcs';
  bucket_name: string;
  region: string;
  cdn_url: string | null;
}

export interface SearchConfig {
  provider: 'postgresql' | 'elasticsearch' | 'opensearch';
  index_name: string;
  min_score: number;
  fuzziness: number;
}

export interface RecommendationConfig {
  enabled: boolean;
  strategy: 'hybrid' | 'content_based' | 'collaborative';
  min_match_score: number;
  max_results: number;
}

export interface AnalyticsConfig {
  enabled: boolean;
  provider: string;
  tracking_id: string | null;
  sample_rate: number;
}

export interface MaintenanceConfig {
  maintenance_mode: boolean;
  maintenance_message: string;
  scheduled_maintenance: string | null;
}

export interface EnvironmentInfo {
  name: 'development' | 'staging' | 'production';
  version: string;
  deploy_time: string;
  git_commit: string;
}
