import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Skeleton } from '@/components/ui/skeleton';
import { formatDistanceToNow } from 'date-fns';
import { Link } from 'react-router-dom';

interface RecentApplication {
  id: string;
  candidate_name: string;
  candidate_email: string;
  job_title: string;
  job_id: string;
  status: string;
  applied_at: string;
  match_score?: number;
}

interface RecentApplicationsProps {
  applications?: RecentApplication[];
  isLoading?: boolean;
}

export function RecentApplications({
  applications = [],
  isLoading = false,
}: RecentApplicationsProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'submitted':
        return 'bg-blue-500/10 text-blue-500 hover:bg-blue-500/20';
      case 'under_review':
        return 'bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20';
      case 'shortlisted':
        return 'bg-green-500/10 text-green-500 hover:bg-green-500/20';
      case 'rejected':
        return 'bg-red-500/10 text-red-500 hover:bg-red-500/20';
      case 'hired':
        return 'bg-purple-500/10 text-purple-500 hover:bg-purple-500/20';
      default:
        return 'bg-gray-500/10 text-gray-500 hover:bg-gray-500/20';
    }
  };

  const getStatusLabel = (status: string) => {
    return status
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Applications</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center gap-4">
                <Skeleton className="h-10 w-10 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3 w-24" />
                </div>
                <Skeleton className="h-6 w-20" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (applications.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Applications</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            No recent applications
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Applications</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {applications.slice(0, 5).map((application) => (
            <div
              key={application.id}
              className="flex items-center gap-4 p-3 rounded-lg hover:bg-accent transition-colors"
            >
              <Avatar className="h-10 w-10">
                <AvatarImage src="/placeholder-avatar.png" />
                <AvatarFallback>
                  {application.candidate_name
                    .split(' ')
                    .map((n) => n[0])
                    .join('')}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{application.candidate_name}</p>
                <p className="text-sm text-muted-foreground truncate">
                  {application.job_title}
                </p>
              </div>
              {application.match_score && (
                <Badge variant="outline" className="mr-2">
                  {Math.round(application.match_score * 100)}% match
                </Badge>
              )}
              <Badge className={getStatusColor(application.status)}>
                {getStatusLabel(application.status)}
              </Badge>
              <div className="text-xs text-muted-foreground whitespace-nowrap">
                {formatDistanceToNow(new Date(application.applied_at), {
                  addSuffix: true,
                })}
              </div>
              <Link to={`/recruiter/applications/${application.id}`}>
                <Button variant="ghost" size="sm">
                  View
                </Button>
              </Link>
            </div>
          ))}
        </div>
        {applications.length > 5 && (
          <div className="mt-4 pt-4 border-t">
            <Link to="/recruiter/applications">
              <Button variant="outline" className="w-full">
                View All Applications
              </Button>
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
