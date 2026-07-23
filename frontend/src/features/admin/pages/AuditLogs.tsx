import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { useAuditLogs } from '../hooks/useAuditLogs';
import { Search, Filter, FileText, RefreshCw, Clock, User, Shield, Server } from 'lucide-react';

export default function AuditLogs() {
  const [actionFilter, setActionFilter] = useState<string>('');
  const [actorFilter, setActorFilter] = useState<string>('');
  const [resourceFilter, setResourceFilter] = useState<string>('');

  const { data: logsData, isLoading, refetch } = useAuditLogs({
    action: actionFilter || undefined,
    actor: actorFilter || undefined,
    resource_type: resourceFilter || undefined,
  });

  const getActorBadge = (actorType: string) => {
    const colors = {
      user: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      admin: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
      system: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
    };
    return (
      <Badge className={colors[actorType as keyof typeof colors] || colors.system} variant="outline">
        {actorType}
      </Badge>
    );
  };

  const getActionIcon = (action: string) => {
    const actions: Record<string, React.ReactNode> = {
      create: <User className="h-4 w-4" />,
      update: <Shield className="h-4 w-4" />,
      delete: <Server className="h-4 w-4" />,
      login: <User className="h-4 w-4" />,
      logout: <User className="h-4 w-4" />,
    };
    return actions[action] || <Clock className="h-4 w-4" />;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Audit Logs</h1>
          <p className="text-slate-400 mt-2">Track administrative actions and system events</p>
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
                  placeholder="Search logs..."
                  className="pl-10 border-slate-700 bg-slate-800/50"
                />
              </div>
            </div>
            <div className="flex gap-2 flex-wrap">
              <Select value={actionFilter} onValueChange={setActionFilter}>
                <SelectTrigger className="w-40 border-slate-700 bg-slate-800/50">
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Action" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Actions</SelectItem>
                  <SelectItem value="create">Create</SelectItem>
                  <SelectItem value="update">Update</SelectItem>
                  <SelectItem value="delete">Delete</SelectItem>
                  <SelectItem value="login">Login</SelectItem>
                  <SelectItem value="logout">Logout</SelectItem>
                </SelectContent>
              </Select>
              <Select value={actorFilter} onValueChange={setActorFilter}>
                <SelectTrigger className="w-40 border-slate-700 bg-slate-800/50">
                  <SelectValue placeholder="Actor" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Actors</SelectItem>
                  <SelectItem value="user">User</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="system">System</SelectItem>
                </SelectContent>
              </Select>
              <Select value={resourceFilter} onValueChange={setResourceFilter}>
                <SelectTrigger className="w-40 border-slate-700 bg-slate-800/50">
                  <SelectValue placeholder="Resource" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Resources</SelectItem>
                  <SelectItem value="user">User</SelectItem>
                  <SelectItem value="job">Job</SelectItem>
                  <SelectItem value="company">Company</SelectItem>
                  <SelectItem value="resume">Resume</SelectItem>
                  <SelectItem value="application">Application</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Audit Logs Table */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle>Audit Trail</CardTitle>
          <CardDescription>
            {logsData ? `${logsData.count} events found` : 'Loading logs...'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-16" />
              ))}
            </div>
          ) : logsData && logsData.results.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-800">
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Actor</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Resource</TableHead>
                    <TableHead>Details</TableHead>
                    <TableHead>IP Address</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {logsData.results.map((log) => (
                    <TableRow key={log.id} className="border-slate-800">
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4 text-slate-400" />
                          {new Date(log.timestamp).toLocaleString()}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getActorBadge(log.actor_type)}
                          <span className="font-medium">{log.actor}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getActionIcon(log.action)}
                          <span className="capitalize">{log.action}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="font-medium capitalize">{log.resource_type}</p>
                          {log.resource_id && (
                            <p className="text-sm text-slate-400 font-mono">{log.resource_id.slice(0, 8)}...</p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <p className="text-sm text-slate-400 max-w-xs truncate">
                          {JSON.stringify(log.details)}
                        </p>
                      </TableCell>
                      <TableCell>
                        <p className="text-sm text-slate-400 font-mono">{log.ip_address || 'N/A'}</p>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">No audit logs found</p>
              <p className="text-sm text-slate-500 mt-2">
                Audit logging requires backend support
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
