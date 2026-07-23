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
import { useAdminResumes, useUpdateResume } from '../hooks/useAdminResumes';
import { Search, Filter, FileText, RefreshCw, UserX, UserCheck } from 'lucide-react';
import type { AdminResume, AdminResumeUpdate } from '../types';

export default function ResumeAdministration() {
  const [search, setSearch] = useState('');
  const [parsedFilter, setParsedFilter] = useState<string>('');
  const [structuredFilter, setStructuredFilter] = useState<string>('');
  const [selectedResume, setSelectedResume] = useState<AdminResume | null>(null);
  const [actionDialog, setActionDialog] = useState<{ open: boolean; action: 'suspend' | 'activate' }>({
    open: false,
    action: 'suspend',
  });
  const [reason, setReason] = useState('');

  const { data: resumesData, isLoading, refetch } = useAdminResumes({
    parsed: parsedFilter ? parsedFilter === 'true' : undefined,
    structured: structuredFilter ? structuredFilter === 'true' : undefined,
  });

  const updateResume = useUpdateResume();

  const handleAction = async () => {
    if (!selectedResume) return;

    let update: AdminResumeUpdate = { reason };

    if (actionDialog.action === 'suspend') {
      update.is_active = false;
    } else if (actionDialog.action === 'activate') {
      update.is_active = true;
    }

    try {
      await updateResume.mutateAsync({ id: selectedResume.id, update });
      setActionDialog({ open: false, action: 'suspend' });
      setReason('');
      setSelectedResume(null);
    } catch (error) {
      console.error('Failed to update resume:', error);
    }
  };

  const openActionDialog = (resume: AdminResume, action: 'suspend' | 'activate') => {
    setSelectedResume(resume);
    setActionDialog({ open: true, action });
    setReason('');
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Resume Administration</h1>
          <p className="text-slate-400 mt-2">View, search, and manage candidate resumes</p>
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
                  placeholder="Search resumes..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-10 border-slate-700 bg-slate-800/50"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Select value={parsedFilter} onValueChange={setParsedFilter}>
                <SelectTrigger className="w-40 border-slate-700 bg-slate-800/50">
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Parsed" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All</SelectItem>
                  <SelectItem value="true">Parsed</SelectItem>
                  <SelectItem value="false">Not Parsed</SelectItem>
                </SelectContent>
              </Select>
              <Select value={structuredFilter} onValueChange={setStructuredFilter}>
                <SelectTrigger className="w-40 border-slate-700 bg-slate-800/50">
                  <SelectValue placeholder="Structured" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All</SelectItem>
                  <SelectItem value="true">Structured</SelectItem>
                  <SelectItem value="false">Not Structured</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Resumes Table */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle>Resumes</CardTitle>
          <CardDescription>
            {resumesData ? `${resumesData.count} resumes found` : 'Loading resumes...'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-16" />
              ))}
            </div>
          ) : resumesData && resumesData.results.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-800">
                    <TableHead>Candidate</TableHead>
                    <TableHead>File Name</TableHead>
                    <TableHead>Size</TableHead>
                    <TableHead>Parsed</TableHead>
                    <TableHead>Structured</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {resumesData.results.map((resume) => (
                    <TableRow key={resume.id} className="border-slate-800">
                      <TableCell>
                        <div>
                          <p className="font-medium">{resume.user_name || resume.user_email}</p>
                          <p className="text-sm text-slate-400">{resume.user_email}</p>
                        </div>
                      </TableCell>
                      <TableCell>{resume.file_name || 'N/A'}</TableCell>
                      <TableCell>{(resume.file_size / 1024).toFixed(1)} KB</TableCell>
                      <TableCell>
                        <Badge className={resume.is_parsed ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'} variant="outline">
                          {resume.is_parsed ? 'Yes' : 'No'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={resume.has_structured_data ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'} variant="outline">
                          {resume.has_structured_data ? 'Yes' : 'No'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {new Date(resume.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openActionDialog(resume, 'suspend')}
                            className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                          >
                            <UserX className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openActionDialog(resume, 'activate')}
                            className="text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10"
                          >
                            <UserCheck className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">No resumes found</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Action Dialog */}
      <Dialog open={actionDialog.open} onOpenChange={(open) => setActionDialog({ ...actionDialog, open })}>
        <DialogContent className="border-slate-800 bg-slate-900">
          <DialogHeader>
            <DialogTitle>
              {actionDialog.action === 'suspend' ? 'Suspend Resume' : 'Activate Resume'}
            </DialogTitle>
            <DialogDescription>
              {actionDialog.action === 'suspend'
                ? 'Suspend this resume. The associated user account will be deactivated.'
                : 'Activate this resume. The associated user account will be reactivated.'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {selectedResume && (
              <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                <p className="font-medium">{selectedResume.user_name || selectedResume.user_email}</p>
                <p className="text-sm text-slate-400">{selectedResume.user_email}</p>
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
              onClick={() => setActionDialog({ open: false, action: 'suspend' })}
              className="border-slate-700"
            >
              Cancel
            </Button>
            <Button
              onClick={handleAction}
              disabled={updateResume.isPending || !reason.trim()}
              className={actionDialog.action === 'suspend' ? 'bg-red-500 hover:bg-red-600' : ''}
            >
              {updateResume.isPending ? 'Processing...' : 'Confirm'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
