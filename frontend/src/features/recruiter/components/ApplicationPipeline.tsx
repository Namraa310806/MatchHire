import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Skeleton } from '@/components/ui/skeleton';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useJobApplications, useUpdateApplicationStatus } from '../hooks';
import { useParams } from 'react-router-dom';
import { Star, Calendar, ChevronRight, FileText } from 'lucide-react';
import { format } from 'date-fns';

const PIPELINE_STAGES = [
  { value: 'submitted', label: 'Submitted', color: 'bg-blue-500/10 text-blue-500' },
  { value: 'under_review', label: 'Under Review', color: 'bg-yellow-500/10 text-yellow-500' },
  { value: 'shortlisted', label: 'Shortlisted', color: 'bg-purple-500/10 text-purple-500' },
  { value: 'rejected', label: 'Rejected', color: 'bg-red-500/10 text-red-500' },
  { value: 'hired', label: 'Hired', color: 'bg-green-500/10 text-green-500' },
];

export function ApplicationPipeline() {
  const { id: jobId } = useParams<{ id: string }>();
  const { data: applications, isLoading } = useJobApplications(jobId || '');
  const updateStatus = useUpdateApplicationStatus();

  const handleStatusChange = async (applicationId: string, newStatus: string) => {
    try {
      await updateStatus.mutateAsync({ id: applicationId, data: { status: newStatus as any } });
    } catch (error) {
      console.error('Failed to update status:', error);
    }
  };


  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <Skeleton className="h-12 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!applications || applications.length === 0) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No applications yet</h3>
          <p className="text-muted-foreground">
            Candidates will appear here once they apply to this job
          </p>
        </CardContent>
      </Card>
    );
  }

  // Group applications by stage
  const groupedApplications = PIPELINE_STAGES.reduce((acc, stage) => {
    acc[stage.value] = applications.filter((app) => app.status === stage.value);
    return acc;
  }, {} as Record<string, typeof applications>);

  return (
    <div className="space-y-6">
      {/* Pipeline Overview */}
      <div className="grid gap-4 md:grid-cols-5">
        {PIPELINE_STAGES.map((stage) => {
          const count = groupedApplications[stage.value]?.length || 0;
          return (
            <Card key={stage.value} className={count > 0 ? 'ring-2 ring-primary' : ''}>
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold">{count}</p>
                <p className="text-sm text-muted-foreground">{stage.label}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Applications by Stage */}
      {PIPELINE_STAGES.map((stage) => {
        const stageApplications = groupedApplications[stage.value] || [];
        if (stageApplications.length === 0) return null;

        return (
          <Card key={stage.value}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${stage.color.split(' ')[0]}`} />
                {stage.label}
                <Badge variant="secondary">{stageApplications.length}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {stageApplications.map((application) => (
                <div
                  key={application.id}
                  className="flex items-center gap-4 p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <Avatar className="h-12 w-12">
                    <AvatarImage src="/placeholder-avatar.png" />
                    <AvatarFallback>
                      {application.candidate_details?.first_name && application.candidate_details?.last_name
                        ? `${application.candidate_details.first_name[0]}${application.candidate_details.last_name[0]}`
                        : 'C'}
                    </AvatarFallback>
                  </Avatar>

                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold">
                        {application.candidate_details?.first_name} {application.candidate_details?.last_name}
                      </h4>
                      {application.match_score && (
                        <Badge variant="outline" className="flex items-center gap-1">
                          <Star className="h-3 w-3 fill-yellow-500 text-yellow-500" />
                          {Math.round(application.match_score * 100)}%
                        </Badge>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-4 text-sm text-muted-foreground mb-2">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-4 w-4" />
                        Applied {format(new Date(application.created_at), 'MMM d, yyyy')}
                      </div>
                      {application.resume_version && (
                        <div className="flex items-center gap-1">
                          <FileText className="h-4 w-4" />
                          Resume v{application.resume_version}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <Select
                      value={application.status}
                      onValueChange={(value) => handleStatusChange(application.id, value)}
                    >
                      <SelectTrigger className="w-[160px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {PIPELINE_STAGES.map((s) => (
                          <SelectItem key={s.value} value={s.value}>
                            {s.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Button variant="outline" size="icon">
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
