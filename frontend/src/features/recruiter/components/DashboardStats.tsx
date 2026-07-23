import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { StatCard } from '@/components/ui/stat-card';
import { Briefcase, Users, FileText, Calendar, TrendingUp } from 'lucide-react';
import { useDashboardStats } from '../hooks';
import { Skeleton } from '@/components/ui/skeleton';

export function DashboardStats() {
  const { data: stats, isLoading } = useDashboardStats();

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(6)].map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-4" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const statCards = [
    {
      title: 'Total Jobs',
      value: stats?.total_jobs || 0,
      icon: Briefcase,
      description: 'Active and draft jobs',
    },
    {
      title: 'Active Jobs',
      value: stats?.active_jobs || 0,
      icon: TrendingUp,
      description: 'Currently published',
    },
    {
      title: 'Total Applications',
      value: stats?.total_applications || 0,
      icon: FileText,
      description: 'All time applications',
    },
    {
      title: 'Pending Review',
      value: stats?.pending_applications || 0,
      icon: Users,
      description: 'Awaiting your review',
    },
    {
      title: 'Shortlisted',
      value: stats?.shortlisted_candidates || 0,
      icon: Users,
      description: 'Candidates shortlisted',
    },
    {
      title: 'Scheduled Interviews',
      value: stats?.scheduled_interviews || 0,
      icon: Calendar,
      description: 'Upcoming interviews',
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
      {statCards.map((stat) => {
        const Icon = stat.icon;
        return (
          <StatCard
            key={stat.title}
            title={stat.title}
            value={stat.value}
            icon={Icon}
            description={stat.description}
          />
        );
      })}
    </div>
  );
}
