import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { useAdminApplications } from '../hooks/useAdminApplications';
import { Search, Filter, FileText, RefreshCw } from 'lucide-react';

export default function ApplicationAdministration() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');

  const { data: applicationsData, isLoading, refetch } = useAdminApplications({
    status: statusFilter || undefined,
  });

  const getStatusBadge = (status: string) => {
    const colors = {
      submitted: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      under_review: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      shortlisted: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      rejected: 'bg-red-500/10 text-red-400 border-red-500/20',
      hired: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    };
    return (
      <Badge className={colors[status as keyof typeof colors] || colors.submitted} variant="outline">
        {status.replace('_', ' ')}
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Application Administration</h1>
          <p className="text-slate-400 mt-2">View and monitor all platform applications</p>
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
                  placeholder="Search applications..."
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
                  <SelectItem value="submitted">Submitted</SelectItem>
                  <SelectItem value="under_review">Under Review</SelectItem>
                  <SelectItem value="shortlisted">Shortlisted</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                  <SelectItem value="hired">Hired</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Applications Table */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle>Applications</CardTitle>
          <CardDescription>
            {applicationsData ? `${applicationsData.count} applications found` : 'Loading applications...'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-16" />
              ))}
            </div>
          ) : applicationsData && applicationsData.results.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-800">
                    <TableHead>Candidate</TableHead>
                    <TableHead>Job</TableHead>
                    <TableHead>Company</TableHead>
                    <TableHead>Recruiter</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Applied</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {applicationsData.results.map((app) => (
                    <TableRow key={app.id} className="border-slate-800">
                      <TableCell>
                        <div>
                          <p className="font-medium">{app.candidate_name || app.candidate_email}</p>
                          <p className="text-sm text-slate-400">{app.candidate_email}</p>
                        </div>
                      </TableCell>
                      <TableCell>{app.job_title}</TableCell>
                      <TableCell>{app.company_name}</TableCell>
                      <TableCell>{app.recruiter_email}</TableCell>
                      <TableCell>{getStatusBadge(app.status)}</TableCell>
                      <TableCell>
                        {new Date(app.created_at).toLocaleDateString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">No applications found</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
