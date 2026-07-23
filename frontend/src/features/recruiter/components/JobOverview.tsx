import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useMyJobs } from '../hooks';
import { Link } from 'react-router-dom';
import { MapPin, DollarSign, Users, TrendingUp } from 'lucide-react';

export function JobOverview() {
  const { data: jobs, isLoading } = useMyJobs();

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500/10 text-green-500 hover:bg-green-500/20';
      case 'draft':
        return 'bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20';
      case 'closed':
        return 'bg-gray-500/10 text-gray-500 hover:bg-gray-500/20';
      default:
        return 'bg-gray-500/10 text-gray-500 hover:bg-gray-500/20';
    }
  };

  const getStatusLabel = (status: string) => {
    return status.charAt(0).toUpperCase() + status.slice(1);
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Your Jobs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="border rounded-lg p-4 space-y-3">
                <Skeleton className="h-5 w-48" />
                <div className="flex gap-4">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-4 w-24" />
                </div>
                <Skeleton className="h-8 w-20" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!jobs || jobs.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Your Jobs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <p className="mb-4">You haven't posted any jobs yet</p>
            <Link to="/recruiter/jobs/new">
              <Button>Create Your First Job</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Your Jobs</CardTitle>
        <Link to="/recruiter/jobs">
          <Button variant="outline" size="sm">
            View All
          </Button>
        </Link>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {jobs.slice(0, 3).map((job) => (
            <div
              key={job.id}
              className="border rounded-lg p-4 hover:bg-accent/50 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">{job.title}</h3>
                  <p className="text-sm text-muted-foreground">{job.company_name}</p>
                </div>
                <Badge className={getStatusColor(job.status)}>
                  {getStatusLabel(job.status)}
                </Badge>
              </div>
              <div className="flex flex-wrap gap-4 text-sm text-muted-foreground mb-3">
                <div className="flex items-center gap-1">
                  <MapPin className="h-4 w-4" />
                  {job.location}
                </div>
                {job.is_remote && (
                  <Badge variant="outline">Remote</Badge>
                )}
                {job.salary_min && job.salary_max && (
                  <div className="flex items-center gap-1">
                    <DollarSign className="h-4 w-4" />
                    ${job.salary_min.toLocaleString()} - ${job.salary_max.toLocaleString()}
                  </div>
                )}
              </div>
              <div className="flex items-center justify-between">
                <div className="flex gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Users className="h-4 w-4" />
                    <span>Applications</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <TrendingUp className="h-4 w-4" />
                    <span>Views</span>
                  </div>
                </div>
                <Link to={`/recruiter/jobs/${job.id}`}>
                  <Button variant="ghost" size="sm">
                    Manage
                  </Button>
                </Link>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
