import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Skeleton } from '@/components/ui/skeleton';
import { useAdminJobs, useUpdateJob } from '../hooks/useAdminJobs';
import { Search, Filter, Briefcase, RefreshCw, CheckCircle, XCircle, Archive } from 'lucide-react';
import type { AdminJob, AdminJobUpdate } from '../types';

export default function JobAdministration() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [selectedJob, setSelectedJob] = useState<AdminJob | null>(null);
  const [actionDialog, setActionDialog] = useState<{ open: boolean; action: 'approve' | 'close' | 'archive' }>({
    open: false,
    action: 'approve',
  });
  const [reason, setReason] = useState('');

  const { data: jobsData, isLoading, refetch } = useAdminJobs({
    search: search || undefined,
    status: statusFilter || undefined,
  });

  const updateJob = useUpdateJob();

  const handleAction = async () => {
    if (!selectedJob) return;

    let update: AdminJobUpdate = { reason };

    if (actionDialog.action === 'approve') {
      update.status = 'active';
    } else if (actionDialog.action === 'close') {
      update.status = 'closed';
    } else if (actionDialog.action === 'archive') {
      update.status = 'archived';
    }

    try {
      await updateJob.mutateAsync({ id: selectedJob.id, update });
      setActionDialog({ open: false, action: 'approve' });
      setReason('');
      setSelectedJob(null);
    } catch (error) {
      console.error('Failed to update job:', error);
    }
  };

  const openActionDialog = (job: AdminJob, action: 'approve' | 'close' | 'archive') => {
    setSelectedJob(job);
    setActionDialog({ open: true, action });
    setReason('');
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      draft: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
      active: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      closed: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      archived: 'bg-red-500/10 text-red-400 border-red-500/20',
    };
    return (
      <Badge className={colors[status as keyof typeof colors] || colors.draft} variant="outline">
        {status}
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Job Administration</h1>
          <p className="text-slate-400 mt-2">View, moderate, and manage platform jobs</p>
        </div>
        <Button variant="outline" onClick={() => refetch()} disabled={isLoading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search by title or company..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-10 border-slate-700 bg-slate-800/50"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-40 border-slate-700 bg-slate-800/50">
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Status</SelectItem>
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="closed">Closed</SelectItem>
                  <SelectItem value="archived">Archived</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Jobs Table */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle>Jobs</CardTitle>
          <CardDescription>
            {jobsData ? `${jobsData.count} jobs found` : 'Loading jobs...'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-16" />
              ))}
            </div>
          ) : jobsData && jobsData.results.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-800">
                    <TableHead>Job</TableHead>
                    <TableHead>Company</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Applications</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jobsData.results.map((job) => (
                    <TableRow key={job.id} className="border-slate-800">
                      <TableCell>
                        <div>
                          <p className="font-medium">{job.title}</p>
                          <p className="text-sm text-slate-400">{job.recruiter_email}</p>
                        </div>
                      </TableCell>
                      <TableCell>{job.company_name}</TableCell>
                      <TableCell>{getStatusBadge(job.status)}</TableCell>
                      <TableCell>{job.applications_count}</TableCell>
                      <TableCell>
                        {new Date(job.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          {job.status === 'draft' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openActionDialog(job, 'approve')}
                              className="text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10"
                            >
                              <CheckCircle className="h-4 w-4" />
                            </Button>
                          )}
                          {job.status === 'active' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openActionDialog(job, 'close')}
                              className="text-amber-400 hover:text-amber-300 hover:bg-amber-500/10"
                            >
                              <XCircle className="h-4 w-4" />
                            </Button>
                          )}
                          {(job.status === 'active' || job.status === 'closed') && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openActionDialog(job, 'archive')}
                              className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                            >
                              <Archive className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="text-center py-12">
              <Briefcase className="h-12 w-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">No jobs found</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Action Dialog */}
      <Dialog open={actionDialog.open} onOpenChange={(open) => setActionDialog({ ...actionDialog, open })}>
        <DialogContent className="border-slate-800 bg-slate-900">
          <DialogHeader>
            <DialogTitle>
              {actionDialog.action === 'approve' && 'Approve Job'}
              {actionDialog.action === 'close' && 'Close Job'}
              {actionDialog.action === 'archive' && 'Archive Job'}
            </DialogTitle>
            <DialogDescription>
              {actionDialog.action === 'approve' && 'Approve this job to make it visible to candidates.'}
              {actionDialog.action === 'close' && 'Close this job. It will no longer accept new applications.'}
              {actionDialog.action === 'archive' && 'Archive this job. It will be hidden from the platform.'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {selectedJob && (
              <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                <p className="font-medium">{selectedJob.title}</p>
                <p className="text-sm text-slate-400">{selectedJob.company_name}</p>
              </div>
            )}
            <div className="space-y-2">
              <Label>Reason</Label>
              <Textarea
                placeholder="Provide a reason for this action..."
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="border-slate-700 bg-slate-800/50 min-h-24"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setActionDialog({ open: false, action: 'approve' })}
              className="border-slate-700"
            >
              Cancel
            </Button>
            <Button
              onClick={handleAction}
              disabled={updateJob.isPending || !reason.trim()}
              className={actionDialog.action === 'archive' ? 'bg-red-500 hover:bg-red-600' : ''}
            >
              {updateJob.isPending ? 'Processing...' : 'Confirm'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
