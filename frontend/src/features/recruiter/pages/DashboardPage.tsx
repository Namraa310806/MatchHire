import { DashboardStats } from '../components/DashboardStats';
import { QuickActions } from '../components/QuickActions';
import { RecentApplications } from '../components/RecentApplications';
import { UpcomingInterviews } from '../components/UpcomingInterviews';
import { ActivityTimeline } from '../components/ActivityTimeline';
import { JobOverview } from '../components/JobOverview';

export function DashboardPage() {
  // Mock recent applications data - in production this would come from an API
  const mockRecentApplications = [
    {
      id: '1',
      candidate_name: 'John Doe',
      candidate_email: 'john@example.com',
      job_title: 'Senior Software Engineer',
      job_id: 'job-1',
      status: 'submitted',
      applied_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      match_score: 0.85,
    },
    {
      id: '2',
      candidate_name: 'Jane Smith',
      candidate_email: 'jane@example.com',
      job_title: 'Product Manager',
      job_id: 'job-2',
      status: 'under_review',
      applied_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      match_score: 0.92,
    },
    {
      id: '3',
      candidate_name: 'Bob Johnson',
      candidate_email: 'bob@example.com',
      job_title: 'Senior Software Engineer',
      job_id: 'job-1',
      status: 'shortlisted',
      applied_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      match_score: 0.78,
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome back! Here's an overview of your hiring activity.
        </p>
      </div>

      <DashboardStats />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <JobOverview />
          <RecentApplications applications={mockRecentApplications} />
        </div>
        <div className="space-y-6">
          <QuickActions />
          <UpcomingInterviews />
          <ActivityTimeline />
        </div>
      </div>
    </div>
  );
}
