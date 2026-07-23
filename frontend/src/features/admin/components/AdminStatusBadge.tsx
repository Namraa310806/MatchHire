import { Badge } from '@/components/ui/badge';

interface AdminStatusBadgeProps {
  status: string;
  variant?: 'default' | 'outline';
}

const statusColors: Record<string, string> = {
  // User/Account Status
  active: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  suspended: 'bg-red-500/10 text-red-400 border-red-500/20',
  pending: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  
  // Job Status
  draft: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  job_active: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  closed: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  archived: 'bg-red-500/10 text-red-400 border-red-500/20',
  
  // Company Status
  approved: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  rejected: 'bg-red-500/10 text-red-400 border-red-500/20',
  
  // Application Status
  submitted: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  under_review: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  shortlisted: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  hired: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  
  // Health Status
  healthy: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  degraded: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  unhealthy: 'bg-red-500/10 text-red-400 border-red-500/20',
  
  // Background Job Status
  running: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  idle: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  failed: 'bg-red-500/10 text-red-400 border-red-500/20',
};

export function AdminStatusBadge({ status, variant = 'outline' }: AdminStatusBadgeProps) {
  const colorClass = statusColors[status.toLowerCase()] || statusColors.pending;
  
  return (
    <Badge className={colorClass} variant={variant}>
      {status.replace('_', ' ')}
    </Badge>
  );
}
