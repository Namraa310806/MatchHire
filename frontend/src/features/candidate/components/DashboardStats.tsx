import { StatCard } from '@/components/ui/stat-card';
import { Briefcase, FileText, Calendar, TrendingUp, Eye, AlertCircle } from 'lucide-react';

interface DashboardStatsProps {
  analytics: {
    total_applications: number;
    total_interviews: number;
    interview_rate: number;
    profile_views: number;
    upcoming_interviews: number;
    saved_jobs: number;
  };
}

export function DashboardStats({ analytics }: DashboardStatsProps) {
  const stats = [
    {
      title: 'Applications',
      value: analytics.total_applications,
      icon: Briefcase,
      trend: { value: 12, isPositive: true },
    },
    {
      title: 'Interviews',
      value: analytics.total_interviews,
      icon: Calendar,
      trend: { value: 5, isPositive: true },
    },
    {
      title: 'Interview Rate',
      value: `${analytics.interview_rate}%`,
      icon: TrendingUp,
      trend: { value: 2, isPositive: true },
    },
    {
      title: 'Profile Views',
      value: analytics.profile_views,
      icon: Eye,
      trend: { value: 8, isPositive: true },
    },
    {
      title: 'Upcoming Interviews',
      value: analytics.upcoming_interviews,
      icon: AlertCircle,
    },
    {
      title: 'Saved Jobs',
      value: analytics.saved_jobs,
      icon: FileText,
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <StatCard
            key={stat.title}
            title={stat.title}
            value={stat.value}
            icon={<Icon className="h-4 w-4" />}
            trend={stat.trend}
          />
        );
      })}
    </div>
  );
}
