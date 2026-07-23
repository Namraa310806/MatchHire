import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useUpcomingInterviews, usePastInterviews } from '../hooks';
import { Link } from 'react-router-dom';
import { Calendar, Clock, Video, MapPin, Phone, ChevronRight, Plus } from 'lucide-react';
import { format } from 'date-fns';

const INTERVIEW_TYPES = {
  video: { icon: Video, label: 'Video Call', color: 'bg-blue-500/10 text-blue-500' },
  phone: { icon: Phone, label: 'Phone Call', color: 'bg-green-500/10 text-green-500' },
  onsite: { icon: MapPin, label: 'In-Person', color: 'bg-purple-500/10 text-purple-500' },
};

export function InterviewCalendar() {
  const { data: upcomingInterviews, isLoading: isLoadingUpcoming } = useUpcomingInterviews();
  const { data: pastInterviews, isLoading: isLoadingPast } = usePastInterviews();

  if (isLoadingUpcoming || isLoadingPast) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Interview Schedule</h2>
          <p className="text-muted-foreground">Manage upcoming and past interviews</p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Schedule Interview
        </Button>
      </div>

      {/* Upcoming Interviews */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Upcoming Interviews
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!upcomingInterviews || upcomingInterviews.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No upcoming interviews scheduled
            </div>
          ) : (
            <div className="space-y-4">
              {upcomingInterviews.map((interview) => {
                const typeInfo = INTERVIEW_TYPES[interview.interview_type as keyof typeof INTERVIEW_TYPES] || INTERVIEW_TYPES.video;
                const TypeIcon = typeInfo.icon;
                
                return (
                  <div
                    key={interview.id}
                    className="flex items-center gap-4 p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className={`p-3 rounded-lg ${typeInfo.color}`}>
                      <TypeIcon className="h-5 w-5" />
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold">
                          {interview.application_details?.candidate_name || 'Unknown Candidate'}
                        </h4>
                        <Badge variant="outline">{typeInfo.label}</Badge>
                      </div>
                      
                      <div className="flex flex-wrap gap-4 text-sm text-muted-foreground mb-2">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          {format(new Date(interview.scheduled_at), 'MMM d, yyyy')}
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          {format(new Date(interview.scheduled_at), 'h:mm a')}
                        </div>
                        {interview.duration_minutes && (
                          <div className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            {interview.duration_minutes} min
                          </div>
                        )}
                      </div>

                      {interview.application_details?.job_title && (
                        <p className="text-sm text-muted-foreground">
                          Interviewing for: {interview.application_details.job_title}
                        </p>
                      )}
                    </div>

                    <div className="flex gap-2">
                      <Button variant="outline" size="sm">
                        Reschedule
                      </Button>
                      <Button variant="outline" size="sm">
                        Cancel
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Past Interviews */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Past Interviews
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!pastInterviews || pastInterviews.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No past interviews
            </div>
          ) : (
            <div className="space-y-4">
              {pastInterviews.slice(0, 5).map((interview) => {
                const typeInfo = INTERVIEW_TYPES[interview.interview_type as keyof typeof INTERVIEW_TYPES] || INTERVIEW_TYPES.video;
                const TypeIcon = typeInfo.icon;
                
                return (
                  <div
                    key={interview.id}
                    className="flex items-center gap-4 p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className={`p-3 rounded-lg ${typeInfo.color} opacity-60`}>
                      <TypeIcon className="h-5 w-5" />
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold">
                          {interview.application_details?.candidate_name || 'Unknown Candidate'}
                        </h4>
                        <Badge variant={interview.status === 'completed' ? 'default' : 'secondary'}>
                          {interview.status}
                        </Badge>
                      </div>
                      
                      <div className="flex flex-wrap gap-4 text-sm text-muted-foreground mb-2">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          {format(new Date(interview.scheduled_at), 'MMM d, yyyy')}
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          {format(new Date(interview.scheduled_at), 'h:mm a')}
                        </div>
                      </div>

                      {interview.application_details?.job_title && (
                        <p className="text-sm text-muted-foreground">
                          Interviewed for: {interview.application_details.job_title}
                        </p>
                      )}
                    </div>

                    <Link to={`/recruiter/interviews/${interview.id}`}>
                      <Button variant="outline" size="icon">
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </Link>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
