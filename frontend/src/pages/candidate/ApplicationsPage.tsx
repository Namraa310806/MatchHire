import { useState } from 'react';
import { useMyApplications, useWithdrawApplication, useApplicationHistory } from '@/features/applications/hooks/useApplications';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Spinner } from '@/components/ui/spinner';
import { EmptyState } from '@/components/ui/empty-state';
import { Briefcase, Clock, CheckCircle, XCircle, AlertCircle, Calendar, FileText, History } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { Link } from 'react-router-dom';

export default function ApplicationsPage() {
  const { data: applications, isLoading } = useMyApplications();
  const withdrawApplication = useWithdrawApplication();
  const [selectedApplication, setSelectedApplication] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState<string | null>(null);

  const handleWithdraw = (id: string) => {
    if (confirm('Are you sure you want to withdraw this application?')) {
      withdrawApplication.mutate(id);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'reviewed':
        return <CheckCircle className="h-4 w-4 text-blue-500" />;
      case 'interview':
        return <Calendar className="h-4 w-4 text-purple-500" />;
      case 'offered':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'rejected':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'withdrawn':
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
      case 'reviewed':
        return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
      case 'interview':
        return 'bg-purple-500/10 text-purple-500 border-purple-500/20';
      case 'offered':
        return 'bg-green-500/10 text-green-500 border-green-500/20';
      case 'rejected':
        return 'bg-red-500/10 text-red-500 border-red-500/20';
      case 'withdrawn':
        return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
      default:
        return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
    }
  };

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
        <h1 className="text-3xl font-bold">My Applications</h1>
        <p className="text-muted-foreground mt-2">Track your job applications</p>
      </div>

      {applications && applications.length > 0 ? (
        <div className="space-y-4">
          {applications.map((application) => (
            <ApplicationCard
              key={application.id}
              application={application}
              onWithdraw={() => handleWithdraw(application.id)}
              onViewHistory={() => setShowHistory(application.id)}
              getStatusIcon={getStatusIcon}
              getStatusColor={getStatusColor}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          title="No applications yet"
          description="Start applying to jobs to track your progress here"
          action={
            <Link to="/candidate/jobs">
              <Button>Browse Jobs</Button>
            </Link>
          }
        />
      )}

      {/* Application History Dialog */}
      <Dialog open={!!showHistory} onOpenChange={() => setShowHistory(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Application History</DialogTitle>
          </DialogHeader>
          <ApplicationHistoryContent applicationId={showHistory!} />
        </DialogContent>
      </Dialog>
    </div>
  );
}

interface ApplicationCardProps {
  application: any;
  onWithdraw: () => void;
  onViewHistory: () => void;
  getStatusIcon: (status: string) => React.ReactNode;
  getStatusColor: (status: string) => string;
}

function ApplicationCard({ application, onWithdraw, onViewHistory, getStatusIcon, getStatusColor }: ApplicationCardProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4 flex-1">
            <div className="p-3 bg-primary/10 rounded-lg">
              <Briefcase className="h-6 w-6 text-primary" />
            </div>
            <div className="flex-1">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-lg">{application.job_details?.title || 'Job Title'}</h3>
                  <p className="text-muted-foreground">{application.job_details?.company || 'Company'}</p>
                </div>
                <Badge className={getStatusColor(application.status)}>
                  <span className="flex items-center gap-1">
                    {getStatusIcon(application.status)}
                    {application.status.charAt(0).toUpperCase() + application.status.slice(1)}
                  </span>
                </Badge>
              </div>
              <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  Applied {formatDistanceToNow(new Date(application.applied_at), { addSuffix: true })}
                </div>
                {application.cover_letter && (
                  <div className="flex items-center gap-1">
                    <FileText className="h-4 w-4" />
                    Cover letter included
                  </div>
                )}
              </div>
              {application.recruiter_notes && (
                <div className="mt-3 p-3 bg-muted rounded-lg">
                  <p className="text-sm font-medium">Recruiter Notes:</p>
                  <p className="text-sm text-muted-foreground">{application.recruiter_notes}</p>
                </div>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={onViewHistory}>
              <History className="h-4 w-4 mr-2" />
              History
            </Button>
            {application.status === 'pending' && (
              <Button variant="outline" size="sm" onClick={onWithdraw}>
                Withdraw
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface ApplicationHistoryContentProps {
  applicationId: string;
}

function ApplicationHistoryContent({ applicationId }: ApplicationHistoryContentProps) {
  const { data: history, isLoading } = useApplicationHistory(applicationId);

  if (isLoading) {
    return <div className="flex justify-center py-8"><Spinner /></div>;
  }

  if (!history || history.length === 0) {
    return <p className="text-sm text-muted-foreground">No history available</p>;
  }

  return (
    <ScrollArea className="h-96">
      <div className="space-y-3">
        {history.map((item) => (
          <div key={item.id} className="flex items-start gap-3 p-3 border rounded-lg">
            <div className="p-2 bg-primary/10 rounded-full">
              <Clock className="h-4 w-4 text-primary" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <p className="font-medium">
                  {item.old_status} → {item.new_status}
                </p>
                <p className="text-xs text-muted-foreground">
                  {formatDistanceToNow(new Date(item.changed_at), { addSuffix: true })}
                </p>
              </div>
              {item.notes && (
                <p className="text-sm text-muted-foreground mt-1">{item.notes}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </ScrollArea>
  );
}
