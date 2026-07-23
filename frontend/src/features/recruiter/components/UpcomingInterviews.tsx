import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Skeleton } from '@/components/ui/skeleton';
import { Calendar, Clock, Video, Phone, MapPin } from 'lucide-react';
import { format } from 'date-fns';
import { Link } from 'react-router-dom';
import { useUpcomingInterviews } from '../hooks';

export function UpcomingInterviews() {
  const { data: interviews, isLoading } = useUpcomingInterviews();

  const getInterviewIcon = (type: string) => {
    switch (type) {
      case 'video':
        return Video;
      case 'phone':
        return Phone;
      case 'onsite':
        return MapPin;
      default:
        return Calendar;
    }
  };

  const getInterviewTypeLabel = (type: string) => {
    switch (type) {
      case 'video':
        return 'Video Call';
      case 'phone':
        return 'Phone Call';
      case 'onsite':
        return 'On-site';
      default:
        return 'Interview';
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Upcoming Interviews</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="flex items-center gap-4">
                <Skeleton className="h-10 w-10 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3 w-24" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!interviews || interviews.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Upcoming Interviews</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            No upcoming interviews scheduled
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upcoming Interviews</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {interviews.slice(0, 5).map((interview) => {
            const Icon = getInterviewIcon(interview.interview_type);
            const candidateName =
              interview.application_details?.candidate_name || 'Candidate';
            const jobTitle =
              interview.application_details?.job_title || 'Job';

            return (
              <div
                key={interview.id}
                className="flex items-center gap-4 p-3 rounded-lg hover:bg-accent transition-colors"
              >
                <Avatar className="h-10 w-10">
                  <AvatarImage src="/placeholder-avatar.png" />
                  <AvatarFallback>
                    {candidateName
                      .split(' ')
                      .map((n) => n[0])
                      .join('')}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{candidateName}</p>
                  <p className="text-sm text-muted-foreground truncate">
                    {jobTitle}
                  </p>
                </div>
                <div className="text-right text-sm">
                  <div className="flex items-center gap-1 text-muted-foreground">
                    <Calendar className="h-3 w-3" />
                    {format(new Date(interview.scheduled_at), 'MMM d')}
                  </div>
                  <div className="flex items-center gap-1 text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    {format(new Date(interview.scheduled_at), 'h:mm a')}
                  </div>
                </div>
                <Badge variant="outline" className="flex items-center gap-1">
                  <Icon className="h-3 w-3" />
                  {getInterviewTypeLabel(interview.interview_type)}
                </Badge>
                <Link to={`/recruiter/interviews/${interview.id}`}>
                  <Button variant="ghost" size="sm">
                    View
                  </Button>
                </Link>
              </div>
            );
          })}
        </div>
        {interviews.length > 5 && (
          <div className="mt-4 pt-4 border-t">
            <Link to="/recruiter/interviews">
              <Button variant="outline" className="w-full">
                View All Interviews
              </Button>
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
