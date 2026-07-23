import { useCandidateProfile } from '@/features/candidate/hooks/useCandidate';
import { useCandidateDashboard } from '@/features/analytics/hooks/useAnalytics';
import { useJobRecommendations } from '@/features/recommendations/hooks/useRecommendations';
import { DashboardStats } from '@/features/candidate/components/DashboardStats';
import { ActivityTimeline } from '@/features/candidate/components/ActivityTimeline';
import { QuickActions } from '@/features/candidate/components/QuickActions';
import { ProfileCompletionCard } from '@/features/candidate/components/ProfileCompletionCard';
import { RecommendedJobs } from '@/features/candidate/components/RecommendedJobs';
import { Spinner } from '@/components/ui/spinner';
import { candidateService } from '@/features/candidate/services/candidateService';

export default function CandidateDashboard() {
  const { data: profile, isLoading: profileLoading } = useCandidateProfile();
  const { data: analytics, isLoading: analyticsLoading } = useCandidateDashboard();
  const { data: recommendations, isLoading: recommendationsLoading } = useJobRecommendations();

  if (profileLoading || analyticsLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner />
      </div>
    );
  }

  const profileCompletion = profile ? candidateService.calculateProfileCompletion(profile) : 0;
  const missingFields = profile ? [
    !profile.title && 'Job title',
    !profile.experience_years && 'Years of experience',
    (!profile.skills || profile.skills.length === 0) && 'Skills',
    !profile.location && 'Location',
    !profile.professional_summary && 'Professional summary',
  ].filter(Boolean) as string[] : [];

  // Mock activity data - in production this would come from the backend
  const activities = [
    {
      id: '1',
      type: 'application' as const,
      description: 'Applied to Senior Software Engineer at Tech Corp',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      status: 'success' as const,
    },
    {
      id: '2',
      type: 'interview' as const,
      description: 'Interview scheduled with Data Systems Inc',
      timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      status: 'pending' as const,
    },
    {
      id: '3',
      type: 'profile_view' as const,
      description: 'Your profile was viewed by a recruiter',
      timestamp: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
      status: 'success' as const,
    },
  ];

  const mockAnalytics = {
    total_applications: analytics?.total_applications ?? 12,
    total_interviews: analytics?.total_interviews ?? 3,
    interview_rate: analytics?.interview_rate ?? 25,
    profile_views: analytics?.profile_views ?? 45,
    upcoming_interviews: analytics?.upcoming_interviews ?? 2,
    saved_jobs: analytics?.saved_jobs ?? 8,
  };

  const mockRecommendations = recommendations?.map((rec: any) => ({
    ...rec.job,
    match_score: rec.score,
    match_reasons: rec.match_reasons,
  })) || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Candidate Dashboard</h1>
        <p className="text-muted-foreground mt-2">Welcome back! Here's your job search overview.</p>
      </div>

      <DashboardStats analytics={mockAnalytics} />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <RecommendedJobs jobs={mockRecommendations} loading={recommendationsLoading} />
          <ActivityTimeline activities={activities} />
        </div>
        <div className="space-y-6">
          <ProfileCompletionCard 
            completion={profileCompletion} 
            missingFields={missingFields}
          />
          <QuickActions />
        </div>
      </div>
    </div>
  );
}
