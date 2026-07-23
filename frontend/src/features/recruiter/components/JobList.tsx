import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { useMyJobs, useCloseJob, useDeleteJob, useDuplicateJob, usePublishJob } from '../hooks';
import { format } from 'date-fns';
import { Link } from 'react-router-dom';
import { MoreHorizontal, Briefcase, Users, TrendingUp, Copy, Archive, Trash2, Eye, Edit } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import React from 'react';
import { toast } from 'sonner';

export function JobList() {
  const { data: jobs, isLoading } = useMyJobs();
  const closeJob = useCloseJob();
  const deleteJob = useDeleteJob();
  const duplicateJob = useDuplicateJob();
  const publishJob = usePublishJob();

  const [statusFilter, setStatusFilter] = React.useState<string>('all');
  const [searchQuery, setSearchQuery] = React.useState('');

  const filteredJobs = React.useMemo(() => {
    if (!jobs) return [];

    return jobs.filter((job) => {
      const matchesStatus = statusFilter === 'all' || job.status === statusFilter;
      const matchesSearch =
        !searchQuery ||
        job.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        job.company_name.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesStatus && matchesSearch;
    });
  }, [jobs, statusFilter, searchQuery]);

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

  const handleCloseJob = async (id: string) => {
    try {
      await closeJob.mutateAsync(id);
      toast.success('Job closed successfully');
    } catch (error) {
      toast.error('Failed to close job');
    }
  };

  const handleDeleteJob = async (id: string) => {
    if (confirm('Are you sure you want to delete this job? This action cannot be undone.')) {
      try {
        await deleteJob.mutateAsync(id);
        toast.success('Job deleted successfully');
      } catch (error) {
        toast.error('Failed to delete job');
      }
    }
  };

  const handleDuplicateJob = async (id: string) => {
    try {
      await duplicateJob.mutateAsync(id);
      toast.success('Job duplicated successfully');
    } catch (error) {
      toast.error('Failed to duplicate job');
    }
  };

  const handlePublishJob = async (id: string) => {
    try {
      await publishJob.mutateAsync(id);
      toast.success('Job published successfully');
    } catch (error) {
      toast.error('Failed to publish job');
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <Skeleton className="h-6 w-48 mb-4" />
              <Skeleton className="h-4 w-32 mb-2" />
              <Skeleton className="h-4 w-24" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!jobs || jobs.length === 0) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <Briefcase className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No jobs yet</h3>
          <p className="text-muted-foreground mb-4">
            Create your first job posting to start attracting candidates
          </p>
          <Link to="/recruiter/jobs/new">
            <Button>Create Job</Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex gap-4">
        <Input
          placeholder="Search jobs..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="max-w-sm"
        />
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="closed">Closed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Job List */}
      <div className="space-y-4">
        {filteredJobs.map((job) => (
          <Card key={job.id}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold">{job.title}</h3>
                    <Badge className={getStatusColor(job.status)}>
                      {getStatusLabel(job.status)}
                    </Badge>
                    {job.is_remote && (
                      <Badge variant="outline">Remote</Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">
                    {job.company_name} • {job.location}
                  </p>
                  <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Users className="h-4 w-4" />
                      <span>Applications</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <TrendingUp className="h-4 w-4" />
                      <span>Views</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Briefcase className="h-4 w-4" />
                      <span>Posted {format(new Date(job.created_at), 'MMM d, yyyy')}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Link to={`/recruiter/jobs/${job.id}`}>
                    <Button variant="outline" size="sm">
                      <Eye className="h-4 w-4 mr-2" />
                      View
                    </Button>
                  </Link>
                  <Link to={`/recruiter/jobs/${job.id}/edit`}>
                    <Button variant="outline" size="sm">
                      <Edit className="h-4 w-4 mr-2" />
                      Edit
                    </Button>
                  </Link>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuLabel>Actions</DropdownMenuLabel>
                      <DropdownMenuSeparator />
                      {job.status === 'draft' && (
                        <DropdownMenuItem onClick={() => handlePublishJob(job.id)}>
                          <Briefcase className="h-4 w-4 mr-2" />
                          Publish
                        </DropdownMenuItem>
                      )}
                      {job.status === 'active' && (
                        <DropdownMenuItem onClick={() => handleCloseJob(job.id)}>
                          <Archive className="h-4 w-4 mr-2" />
                          Close
                        </DropdownMenuItem>
                      )}
                      <DropdownMenuItem onClick={() => handleDuplicateJob(job.id)}>
                        <Copy className="h-4 w-4 mr-2" />
                        Duplicate
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={() => handleDeleteJob(job.id)}
                        className="text-red-600"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredJobs.length === 0 && jobs.length > 0 && (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-muted-foreground">No jobs match your filters</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
