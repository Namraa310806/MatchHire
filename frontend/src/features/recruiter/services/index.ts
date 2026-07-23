export { recruiterService } from './recruiterService';
export { jobService } from './jobService';
export { applicationService } from './applicationService';
export { interviewService } from './interviewService';
export { searchService } from './searchService';
export { recommendationService } from './recommendationService';
export { analyticsService } from './analyticsService';
export { notificationService } from './notificationService';

export type {
  RecruiterProfile,
  RecruiterProfileUpdate,
  DashboardStats,
  RecentActivity,
} from './recruiterService';

export type {
  Job,
  JobCreate,
  JobUpdate,
  JobSearchParams,
  PaginatedJobs,
} from './jobService';

export type {
  Application,
  ApplicationStatusUpdate,
  ApplicationStatusHistory,
  ApplicationNote,
} from './applicationService';

export type {
  Interview,
  InterviewCreate,
  InterviewUpdate,
} from './interviewService';

export type {
  CandidateSearchResult,
  CandidateSearchParams,
  PaginatedCandidates,
  SavedSearch,
} from './searchService';

export type {
  CandidateRecommendation,
  SimilarCandidate,
} from './recommendationService';

export type {
  HiringFunnel,
  TimeToHire,
  ApplicationTrend,
  JobPerformance,
  SearchPerformance,
  RecommendationEffectiveness,
  InterviewConversion,
  RecruiterActivity,
  PipelineAnalytics,
} from './analyticsService';

export type {
  Notification,
  NotificationPreferences,
} from './notificationService';
