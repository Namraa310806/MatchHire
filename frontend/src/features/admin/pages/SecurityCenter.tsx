import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useSecurityEvents, useLoginActivity } from '../hooks/useSecurity';
import { Shield, AlertTriangle, Lock, User, Clock, Activity, Fingerprint } from 'lucide-react';

export default function SecurityCenter() {
  const { data: securityEvents, isLoading: eventsLoading } = useSecurityEvents();
  const { data: loginActivity, isLoading: loginLoading } = useLoginActivity();

  const getSeverityBadge = (severity: string) => {
    const colors = {
      low: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
      medium: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      high: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
      critical: 'bg-red-500/10 text-red-400 border-red-500/20',
    };
    return (
      <Badge className={colors[severity as keyof typeof colors] || colors.low} variant="outline">
        {severity}
      </Badge>
    );
  };

  const getEventIcon = (eventType: string) => {
    const icons: Record<string, React.ReactNode> = {
      login_success: <User className="h-4 w-4 text-emerald-400" />,
      login_failure: <AlertTriangle className="h-4 w-4 text-red-400" />,
      account_locked: <Lock className="h-4 w-4 text-red-400" />,
      permission_changed: <Shield className="h-4 w-4 text-amber-400" />,
      role_changed: <Fingerprint className="h-4 w-4 text-amber-400" />,
    };
    return icons[eventType] || <Activity className="h-4 w-4" />;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Security Center</h1>
        <p className="text-slate-400 mt-2">Monitor security events and login activity</p>
      </div>

      {/* Security Events */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Security Events
          </CardTitle>
        </CardHeader>
        <CardContent>
          {eventsLoading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-16" />
              ))}
            </div>
          ) : securityEvents && securityEvents.length > 0 ? (
            <div className="space-y-3">
              {securityEvents.map((event) => (
                <div key={event.id} className="flex items-center justify-between p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                  <div className="flex items-center gap-3">
                    {getEventIcon(event.event_type)}
                    <div>
                      <p className="font-medium capitalize">{event.event_type.replace('_', ' ')}</p>
                      <p className="text-sm text-slate-400">
                        {event.user_email || 'System event'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    {getSeverityBadge(event.severity)}
                    <p className="text-sm text-slate-400">
                      {new Date(event.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Shield className="h-12 w-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">No security events recorded</p>
              <p className="text-sm text-slate-500 mt-2">
                Security event tracking requires backend support
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Login Activity */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Login Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loginLoading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-16" />
              ))}
            </div>
          ) : loginActivity && loginActivity.length > 0 ? (
            <div className="space-y-3">
              {loginActivity.map((activity) => (
                <div key={activity.user_id} className="flex items-center justify-between p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                  <div className="flex items-center gap-3">
                    <User className="h-4 w-4 text-slate-400" />
                    <div>
                      <p className="font-medium">{activity.user_email}</p>
                      <p className="text-sm text-slate-400">
                        Last login: {new Date(activity.last_login).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-6 text-sm">
                    <div className="text-center">
                      <p className="font-medium">{activity.login_count}</p>
                      <p className="text-slate-400">Logins</p>
                    </div>
                    <div className="text-center">
                      <p className="font-medium text-red-400">{activity.failed_attempts}</p>
                      <p className="text-slate-400">Failed</p>
                    </div>
                    {activity.current_session_ip && (
                      <div className="text-right">
                        <p className="font-mono text-sm">{activity.current_session_ip}</p>
                        <p className="text-slate-400">Current IP</p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Clock className="h-12 w-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">No login activity data available</p>
              <p className="text-sm text-slate-500 mt-2">
                Login activity tracking requires backend support
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Security Summary */}
      <div className="grid gap-6 md:grid-cols-3">
        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Activity className="h-4 w-4" />
              Active Sessions
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loginLoading ? (
              <Skeleton className="h-12" />
            ) : (
              <p className="text-3xl font-bold">
                {loginActivity?.filter(a => a.current_session_ip).length || 0}
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <AlertTriangle className="h-4 w-4" />
              Failed Attempts
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loginLoading ? (
              <Skeleton className="h-12" />
            ) : (
              <p className="text-3xl font-bold text-red-400">
                {loginActivity?.reduce((sum, a) => sum + a.failed_attempts, 0) || 0}
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Shield className="h-4 w-4" />
              Security Events
            </CardTitle>
          </CardHeader>
          <CardContent>
            {eventsLoading ? (
              <Skeleton className="h-12" />
            ) : (
              <p className="text-3xl font-bold">
                {securityEvents?.length || 0}
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
