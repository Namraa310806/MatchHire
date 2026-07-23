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
import { useAdminCompanies, useUpdateCompany } from '../hooks/useAdminCompanies';
import { Search, Filter, Building2, RefreshCw, CheckCircle, XCircle, Ban, Users, Briefcase } from 'lucide-react';
import type { AdminCompany, AdminCompanyUpdate } from '../types';

export default function CompanyManagement() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [selectedCompany, setSelectedCompany] = useState<AdminCompany | null>(null);
  const [actionDialog, setActionDialog] = useState<{ open: boolean; action: 'approve' | 'reject' | 'suspend' }>({
    open: false,
    action: 'approve',
  });
  const [reason, setReason] = useState('');

  const { data: companiesData, isLoading, refetch } = useAdminCompanies({
    search: search || undefined,
    status: statusFilter || undefined,
  });

  const updateCompany = useUpdateCompany();

  const handleAction = async () => {
    if (!selectedCompany) return;

    let update: AdminCompanyUpdate = { reason };

    if (actionDialog.action === 'approve') {
      update.status = 'approved';
    } else if (actionDialog.action === 'reject') {
      update.status = 'rejected';
    } else if (actionDialog.action === 'suspend') {
      update.status = 'suspended';
    }

    try {
      await updateCompany.mutateAsync({ id: selectedCompany.id, update });
      setActionDialog({ open: false, action: 'approve' });
      setReason('');
      setSelectedCompany(null);
    } catch (error) {
      console.error('Failed to update company:', error);
    }
  };

  const openActionDialog = (company: AdminCompany, action: 'approve' | 'reject' | 'suspend') => {
    setSelectedCompany(company);
    setActionDialog({ open: true, action });
    setReason('');
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      pending: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      approved: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      rejected: 'bg-red-500/10 text-red-400 border-red-500/20',
      suspended: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
    };
    return (
      <Badge className={colors[status as keyof typeof colors] || colors.pending} variant="outline">
        {status}
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Company Management</h1>
          <p className="text-slate-400 mt-2">View, approve, and manage platform companies</p>
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
                  placeholder="Search by name or website..."
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
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="approved">Approved</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                  <SelectItem value="suspended">Suspended</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Companies Table */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle>Companies</CardTitle>
          <CardDescription>
            {companiesData ? `${companiesData.count} companies found` : 'Loading companies...'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-16" />
              ))}
            </div>
          ) : companiesData && companiesData.results.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-800">
                    <TableHead>Company</TableHead>
                    <TableHead>Industry</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Recruiters</TableHead>
                    <TableHead>Jobs</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {companiesData.results.map((company) => (
                    <TableRow key={company.id} className="border-slate-800">
                      <TableCell>
                        <div className="flex items-center gap-3">
                          {company.logo_url && (
                            <img
                              src={company.logo_url}
                              alt={company.name}
                              className="h-8 w-8 rounded object-cover"
                            />
                          )}
                          <div>
                            <p className="font-medium">{company.name}</p>
                            <p className="text-sm text-slate-400">{company.website || 'No website'}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{company.industry || 'N/A'}</TableCell>
                      <TableCell>{company.location || 'N/A'}</TableCell>
                      <TableCell>{getStatusBadge(company.status)}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Users className="h-4 w-4 text-slate-400" />
                          {company.recruiter_count}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Briefcase className="h-4 w-4 text-slate-400" />
                          {company.job_count}
                        </div>
                      </TableCell>
                      <TableCell>
                        {new Date(company.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          {company.status === 'pending' && (
                            <>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => openActionDialog(company, 'approve')}
                                className="text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10"
                              >
                                <CheckCircle className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => openActionDialog(company, 'reject')}
                                className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                              >
                                <XCircle className="h-4 w-4" />
                              </Button>
                            </>
                          )}
                          {company.status === 'approved' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openActionDialog(company, 'suspend')}
                              className="text-amber-400 hover:text-amber-300 hover:bg-amber-500/10"
                            >
                              <Ban className="h-4 w-4" />
                            </Button>
                          )}
                          {company.status === 'suspended' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openActionDialog(company, 'approve')}
                              className="text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10"
                            >
                              <CheckCircle className="h-4 w-4" />
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
              <Building2 className="h-12 w-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">No companies found</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Action Dialog */}
      <Dialog open={actionDialog.open} onOpenChange={(open) => setActionDialog({ ...actionDialog, open })}>
        <DialogContent className="border-slate-800 bg-slate-900">
          <DialogHeader>
            <DialogTitle>
              {actionDialog.action === 'approve' && 'Approve Company'}
              {actionDialog.action === 'reject' && 'Reject Company'}
              {actionDialog.action === 'suspend' && 'Suspend Company'}
            </DialogTitle>
            <DialogDescription>
              {actionDialog.action === 'approve' && 'Approve this company to allow recruiters to post jobs.'}
              {actionDialog.action === 'reject' && 'Reject this company. It will not be able to operate on the platform.'}
              {actionDialog.action === 'suspend' && 'Suspend this company. All associated jobs will be hidden.'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {selectedCompany && (
              <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                <p className="font-medium">{selectedCompany.name}</p>
                <p className="text-sm text-slate-400">{selectedCompany.website || 'No website'}</p>
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
              disabled={updateCompany.isPending || !reason.trim()}
              className={
                actionDialog.action === 'reject' || actionDialog.action === 'suspend'
                  ? 'bg-red-500 hover:bg-red-600'
                  : ''
              }
            >
              {updateCompany.isPending ? 'Processing...' : 'Confirm'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
