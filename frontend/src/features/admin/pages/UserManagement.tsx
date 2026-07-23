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
import { useAdminUsers, useUpdateUser } from '../hooks/useAdminUsers';
import { Search, Filter, MoreVertical, Shield, UserX, UserCheck, Crown, RefreshCw } from 'lucide-react';
import type { AdminUser, AdminUserUpdate } from '../types';

export default function UserManagement() {
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [activeFilter, setActiveFilter] = useState<string>('');
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [actionDialog, setActionDialog] = useState<{ open: boolean; action: 'suspend' | 'activate' | 'change_role' }>({
    open: false,
    action: 'suspend',
  });
  const [reason, setReason] = useState('');
  const [newRole, setNewRole] = useState<'candidate' | 'recruiter' | 'admin'>('candidate');

  const { data: usersData, isLoading, refetch } = useAdminUsers({
    search: search || undefined,
    role: roleFilter || undefined,
    is_active: activeFilter ? activeFilter === 'true' : undefined,
  });

  const updateUser = useUpdateUser();

  const handleAction = async () => {
    if (!selectedUser) return;

    let update: AdminUserUpdate = { reason };

    if (actionDialog.action === 'suspend') {
      update.is_active = false;
    } else if (actionDialog.action === 'activate') {
      update.is_active = true;
    } else if (actionDialog.action === 'change_role') {
      update.role = newRole;
    }

    try {
      await updateUser.mutateAsync({ id: selectedUser.id, update });
      setActionDialog({ open: false, action: 'suspend' });
      setReason('');
      setSelectedUser(null);
    } catch (error) {
      console.error('Failed to update user:', error);
    }
  };

  const openActionDialog = (user: AdminUser, action: 'suspend' | 'activate' | 'change_role') => {
    setSelectedUser(user);
    setActionDialog({ open: true, action });
    setReason('');
    if (action === 'change_role') {
      setNewRole(user.role);
    }
  };

  const getRoleBadge = (role: string) => {
    const colors = {
      admin: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
      recruiter: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      candidate: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    };
    return (
      <Badge className={colors[role as keyof typeof colors] || colors.candidate} variant="outline">
        {role}
      </Badge>
    );
  };

  const getStatusBadge = (isActive: boolean) => {
    return (
      <Badge className={isActive ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'} variant="outline">
        {isActive ? 'Active' : 'Suspended'}
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">User Management</h1>
          <p className="text-slate-400 mt-2">View, search, and manage platform users</p>
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
                  placeholder="Search by name or email..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-10 border-slate-700 bg-slate-800/50"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Select value={roleFilter} onValueChange={setRoleFilter}>
                <SelectTrigger className="w-40 border-slate-700 bg-slate-800/50">
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Role" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Roles</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="recruiter">Recruiter</SelectItem>
                  <SelectItem value="candidate">Candidate</SelectItem>
                </SelectContent>
              </Select>
              <Select value={activeFilter} onValueChange={setActiveFilter}>
                <SelectTrigger className="w-40 border-slate-700 bg-slate-800/50">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Status</SelectItem>
                  <SelectItem value="true">Active</SelectItem>
                  <SelectItem value="false">Suspended</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle>Users</CardTitle>
          <CardDescription>
            {usersData ? `${usersData.count} users found` : 'Loading users...'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-16" />
              ))}
            </div>
          ) : usersData && usersData.results.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-800">
                    <TableHead>User</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Joined</TableHead>
                    <TableHead>Last Login</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {usersData.results.map((user) => (
                    <TableRow key={user.id} className="border-slate-800">
                      <TableCell>
                        <div>
                          <p className="font-medium">{user.full_name || user.email}</p>
                          <p className="text-sm text-slate-400">{user.email}</p>
                        </div>
                      </TableCell>
                      <TableCell>{getRoleBadge(user.role)}</TableCell>
                      <TableCell>{getStatusBadge(user.is_active)}</TableCell>
                      <TableCell>
                        {new Date(user.date_joined).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        {user.last_login
                          ? new Date(user.last_login).toLocaleDateString()
                          : 'Never'}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          {user.is_active ? (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openActionDialog(user, 'suspend')}
                              className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                            >
                              <UserX className="h-4 w-4" />
                            </Button>
                          ) : (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openActionDialog(user, 'activate')}
                              className="text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10"
                            >
                              <UserCheck className="h-4 w-4" />
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openActionDialog(user, 'change_role')}
                            className="text-blue-400 hover:text-blue-300 hover:bg-blue-500/10"
                          >
                            <Crown className="h-4 w-4" />
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
              <Shield className="h-12 w-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">No users found</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Action Dialog */}
      <Dialog open={actionDialog.open} onOpenChange={(open) => setActionDialog({ ...actionDialog, open })}>
        <DialogContent className="border-slate-800 bg-slate-900">
          <DialogHeader>
            <DialogTitle>
              {actionDialog.action === 'suspend' && 'Suspend User'}
              {actionDialog.action === 'activate' && 'Activate User'}
              {actionDialog.action === 'change_role' && 'Change Role'}
            </DialogTitle>
            <DialogDescription>
              {actionDialog.action === 'suspend' && 'Suspend this user account. They will not be able to access the platform.'}
              {actionDialog.action === 'activate' && 'Activate this user account. They will regain access to the platform.'}
              {actionDialog.action === 'change_role' && 'Change the role of this user. This will affect their permissions.'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {selectedUser && (
              <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                <p className="font-medium">{selectedUser.full_name || selectedUser.email}</p>
                <p className="text-sm text-slate-400">{selectedUser.email}</p>
              </div>
            )}
            {actionDialog.action === 'change_role' && (
              <div className="space-y-2">
                <Label>Role</Label>
                <Select value={newRole} onValueChange={(value: any) => setNewRole(value)}>
                  <SelectTrigger className="border-slate-700 bg-slate-800/50">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="candidate">Candidate</SelectItem>
                    <SelectItem value="recruiter">Recruiter</SelectItem>
                    <SelectItem value="admin">Admin</SelectItem>
                  </SelectContent>
                </Select>
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
              disabled={updateUser.isPending || !reason.trim()}
              className={actionDialog.action === 'suspend' ? 'bg-red-500 hover:bg-red-600' : ''}
            >
              {updateUser.isPending ? 'Processing...' : 'Confirm'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
