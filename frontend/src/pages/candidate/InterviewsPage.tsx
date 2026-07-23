import { useState } from 'react';
import { useMyInterviews, useInterviewDetails, useUpdateInterviewStatus } from '@/features/interviews/hooks/useInterviews';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Spinner } from '@/components/ui/spinner';
import { EmptyState } from '@/components/ui/empty-state';
import { Calendar, Clock, Video, MapPin, CheckCircle, XCircle, AlertCircle, ExternalLink, FileText } from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';

export default function InterviewsPage() {
  const { data: interviews, isLoading } = useMyInterviews();
  const updateStatus = useUpdateInterviewStatus();
  const [selectedInterview, setSelectedInterview] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'upcoming' | 'past'>('upcoming');

  const handleStatusUpdate = (id: string, status: string) => {
    updateStatus.mutate({ id, status });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'scheduled':
        return <Calendar className="h-4 w-4 text-blue-500" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'cancelled':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'no_show':
        return <AlertCircle className="h-4 w-4 text-orange-500" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'scheduled':
        return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
      case 'completed':
        return 'bg-green-500/10 text-green-500 border-green-500/20';
      case 'cancelled':
        return 'bg-red-500/10 text-red-500 border-red-500/20';
      case 'no_show':
        return 'bg-orange-500/10 text-orange-500 border-orange-500/20';
      default:
        return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
    }
  };

  const filteredInterviews = (interviews || []).filter((interview: any) => {
    if (filter === 'all') return true;
    const now = new Date();
    const interviewDate = new Date(interview.scheduled_at);
    if (filter === 'upcoming') return interviewDate > now;
    if (filter === 'past') return interviewDate <= now;
    return true;
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Interview Center</h1>
        <p className="text-muted-foreground mt-2">Manage your upcoming and past interviews</p>
      </div>

      <div className="flex gap-2">
        <Button
          variant={filter === 'upcoming' ? 'default' : 'outline'}
          onClick={() => setFilter('upcoming')}
        >
          Upcoming
        </Button>
        <Button
          variant={filter === 'past' ? 'default' : 'outline'}
          onClick={() => setFilter('past')}
        >
          Past
        </Button>
        <Button
          variant={filter === 'all' ? 'default' : 'outline'}
          onClick={() => setFilter('all')}
        >
          All
        </Button>
      </div>

      {filteredInterviews.length > 0 ? (
        <div className="space-y-4">
          {filteredInterviews.map((interview: any) => {
            const isUpcoming = new Date(interview.scheduled_at) > new Date();
            return (
              <InterviewCard
                key={interview.id}
                interview={interview}
                onViewDetails={() => setSelectedInterview(interview.id)}
                onUpdateStatus={(status) => handleStatusUpdate(interview.id, status)}
                getStatusIcon={getStatusIcon}
                getStatusColor={getStatusColor}
                isUpcoming={isUpcoming}
              />
            );
          })}
        </div>
      ) : (
        <EmptyState
          title="No interviews found"
          description={filter === 'upcoming' ? 'You have no upcoming interviews scheduled' : 'No interviews to display'}
        />
      )}

      {/* Interview Details Dialog */}
      <Dialog open={!!selectedInterview} onOpenChange={() => setSelectedInterview(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Interview Details</DialogTitle>
          </DialogHeader>
          <InterviewDetailsContent interviewId={selectedInterview!} />
        </DialogContent>
      </Dialog>
    </div>
  );
}

interface InterviewCardProps {
  interview: any;
  onViewDetails: () => void;
  onUpdateStatus: (status: string) => void;
  getStatusIcon: (status: string) => React.ReactNode;
  getStatusColor: (status: string) => string;
  isUpcoming: boolean;
}

function InterviewCard({ interview, onViewDetails, onUpdateStatus, getStatusIcon, getStatusColor, isUpcoming }: InterviewCardProps) {

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4 flex-1">
            <div className="p-3 bg-primary/10 rounded-lg">
              <Video className="h-6 w-6 text-primary" />
            </div>
            <div className="flex-1">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-lg">{interview.job_details?.title || 'Job Interview'}</h3>
                  <p className="text-muted-foreground">{interview.job_details?.company || 'Company'}</p>
                </div>
                <Badge className={getStatusColor(interview.status)}>
                  <span className="flex items-center gap-1">
                    {getStatusIcon(interview.status)}
                    {interview.status.charAt(0).toUpperCase() + interview.status.slice(1)}
                  </span>
                </Badge>
              </div>
              <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  {format(new Date(interview.scheduled_at), 'PPP')}
                </div>
                <div className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  {format(new Date(interview.scheduled_at), 'p')}
                </div>
                <div className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  {interview.duration} minutes
                </div>
              </div>
              <div className="flex items-center gap-2 mt-2">
                {interview.interview_type === 'virtual' && (
                  <Badge variant="outline">Virtual</Badge>
                )}
                {interview.interview_type === 'in_person' && (
                  <Badge variant="outline">In Person</Badge>
                )}
                {interview.location && (
                  <div className="flex items-center gap-1 text-sm text-muted-foreground">
                    <MapPin className="h-4 w-4" />
                    {interview.location}
                  </div>
                )}
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={onViewDetails}>
              <FileText className="h-4 w-4 mr-2" />
              Details
            </Button>
            {interview.meeting_link && (
              <Button variant="outline" size="sm" asChild>
                <a href={interview.meeting_link} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Join
                </a>
              </Button>
            )}
            {isUpcoming && interview.status === 'scheduled' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onUpdateStatus('cancelled')}
              >
                Cancel
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface InterviewDetailsContentProps {
  interviewId: string;
}

function InterviewDetailsContent({ interviewId }: InterviewDetailsContentProps) {
  const { data: interview, isLoading } = useInterviewDetails(interviewId);

  if (isLoading) {
    return <div className="flex justify-center py-8"><Spinner /></div>;
  }

  if (!interview) {
    return <p className="text-sm text-muted-foreground">Interview details not found</p>;
  }

  return (
    <ScrollArea className="h-96">
      <div className="space-y-4">
        <div>
          <p className="text-sm font-medium">Job</p>
          <p className="text-sm text-muted-foreground">{interview.job_details?.title}</p>
          <p className="text-sm text-muted-foreground">{interview.job_details?.company}</p>
        </div>

        <div>
          <p className="text-sm font-medium">Scheduled Time</p>
          <p className="text-sm text-muted-foreground">
            {format(new Date(interview.scheduled_at), 'PPP')}
          </p>
          <p className="text-sm text-muted-foreground">
            {format(new Date(interview.scheduled_at), 'p')}
          </p>
          <p className="text-sm text-muted-foreground">
            Duration: {interview.duration} minutes
          </p>
        </div>

        <div>
          <p className="text-sm font-medium">Interview Type</p>
          <p className="text-sm text-muted-foreground capitalize">{interview.interview_type.replace('_', ' ')}</p>
        </div>

        {interview.location && (
          <div>
            <p className="text-sm font-medium">Location</p>
            <p className="text-sm text-muted-foreground">{interview.location}</p>
          </div>
        )}

        {interview.meeting_link && (
          <div>
            <p className="text-sm font-medium">Meeting Link</p>
            <a
              href={interview.meeting_link}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary hover:underline"
            >
              {interview.meeting_link}
            </a>
          </div>
        )}

        {interview.interviewer_name && (
          <div>
            <p className="text-sm font-medium">Interviewer</p>
            <p className="text-sm text-muted-foreground">{interview.interviewer_name}</p>
          </div>
        )}

        {interview.preparation_notes && (
          <div>
            <p className="text-sm font-medium">Preparation Notes</p>
            <p className="text-sm text-muted-foreground whitespace-pre-wrap">{interview.preparation_notes}</p>
          </div>
        )}

        {interview.feedback && (
          <div>
            <p className="text-sm font-medium">Feedback</p>
            <p className="text-sm text-muted-foreground whitespace-pre-wrap">{interview.feedback}</p>
          </div>
        )}

        <div>
          <p className="text-sm font-medium">Status</p>
          <p className="text-sm text-muted-foreground capitalize">{interview.status}</p>
        </div>

        <div>
          <p className="text-sm font-medium">Created</p>
          <p className="text-sm text-muted-foreground">
            {formatDistanceToNow(new Date(interview.created_at), { addSuffix: true })}
          </p>
        </div>
      </div>
    </ScrollArea>
  );
}
