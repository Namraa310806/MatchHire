import { useCandidateDashboard } from '@/features/analytics/hooks/useAnalytics';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { StatCard } from '@/components/ui/stat-card';
import { Spinner } from '@/components/ui/spinner';
import { TrendingUp, Briefcase, Calendar, Eye, Target, Zap } from 'lucide-react';

export default function AnalyticsPage() {
  const { data: analytics, isLoading } = useCandidateDashboard();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner />
      </div>
    );
  }

  const mockAnalytics = {
    total_applications: analytics?.total_applications ?? 24,
    total_interviews: analytics?.total_interviews ?? 6,
    interview_rate: analytics?.interview_rate ?? 25,
    profile_views: analytics?.profile_views ?? 89,
    upcoming_interviews: analytics?.upcoming_interviews ?? 2,
    saved_jobs: analytics?.saved_jobs ?? 15,
    response_rate: 42,
    avg_response_time: 3,
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Candidate Analytics</h1>
        <p className="text-muted-foreground mt-2">Track your job search performance</p>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Applications Submitted"
          value={mockAnalytics.total_applications}
          icon={<Briefcase className="h-4 w-4" />}
          trend={{ value: 12, isPositive: true }}
        />
        <StatCard
          title="Interviews Scheduled"
          value={mockAnalytics.total_interviews}
          icon={<Calendar className="h-4 w-4" />}
          trend={{ value: 8, isPositive: true }}
        />
        <StatCard
          title="Interview Rate"
          value={`${mockAnalytics.interview_rate}%`}
          icon={<Target className="h-4 w-4" />}
          trend={{ value: 5, isPositive: true }}
        />
        <StatCard
          title="Profile Views"
          value={mockAnalytics.profile_views}
          icon={<Eye className="h-4 w-4" />}
          trend={{ value: 15, isPositive: true }}
        />
      </div>

      {/* Performance Metrics */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Response Performance</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Response Rate</p>
                <p className="text-xs text-muted-foreground">Employers who responded</p>
              </div>
              <p className="text-2xl font-bold">{mockAnalytics.response_rate}%</p>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Avg Response Time</p>
                <p className="text-xs text-muted-foreground">Days to first response</p>
              </div>
              <p className="text-2xl font-bold">{mockAnalytics.avg_response_time}d</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Application Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Pending</p>
                <p className="text-xs text-muted-foreground">Awaiting response</p>
              </div>
              <p className="text-2xl font-bold">12</p>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">In Review</p>
                <p className="text-xs text-muted-foreground">Being reviewed</p>
              </div>
              <p className="text-2xl font-bold">6</p>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Interview Stage</p>
                <p className="text-xs text-muted-foreground">Interview scheduled</p>
              </div>
              <p className="text-2xl font-bold">4</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Skills Insights */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Skills Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">React</span>
                <span className="text-sm text-muted-foreground">85% match</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-primary" style={{ width: '85%' }} />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">TypeScript</span>
                <span className="text-sm text-muted-foreground">78% match</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-primary" style={{ width: '78%' }} />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Node.js</span>
                <span className="text-sm text-muted-foreground">72% match</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-primary" style={{ width: '72%' }} />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Python</span>
                <span className="text-sm text-muted-foreground">65% match</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-primary" style={{ width: '65%' }} />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Application Trend */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Application Trend
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center border rounded-lg bg-muted/20">
            <p className="text-sm text-muted-foreground">Application trend chart would be displayed here</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
