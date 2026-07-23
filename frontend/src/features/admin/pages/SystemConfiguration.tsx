import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { systemConfigApi } from '../services/adminService';
import { useQuery } from '@tanstack/react-query';
import { Settings, Mail, Database, Search, Brain, BarChart3, AlertTriangle } from 'lucide-react';

export default function SystemConfiguration() {
  const { data: config, isLoading } = useQuery({
    queryKey: ['system', 'config'],
    queryFn: systemConfigApi.getSystemConfig,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">System Configuration</h1>
        <p className="text-slate-400 mt-2">Platform settings and configuration (read-only)</p>
      </div>

      {/* Environment Info */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Environment
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-20" />
          ) : config ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Environment</p>
                <Badge className="mt-2 capitalize">{config.environment.name}</Badge>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Version</p>
                <p className="text-lg font-bold mt-1">{config.environment.version}</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Deployed</p>
                <p className="text-lg font-bold mt-1">{new Date(config.environment.deploy_time).toLocaleDateString()}</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Git Commit</p>
                <p className="text-lg font-bold mt-1 font-mono">{config.environment.git_commit.slice(0, 8)}</p>
              </div>
            </div>
          ) : (
            <p className="text-slate-400">Configuration unavailable</p>
          )}
        </CardContent>
      </Card>

      {/* General Settings */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            General Settings
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-40" />
          ) : config ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Site Name</span>
                <span className="font-medium">{config.general.site_name}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Site URL</span>
                <span className="font-medium">{config.general.site_url || 'Not configured'}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Support Email</span>
                <span className="font-medium">{config.general.support_email}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Max Upload Size</span>
                <span className="font-medium">{config.general.max_upload_size_mb} MB</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-slate-400">Allowed File Types</span>
                <span className="font-medium">{config.general.allowed_file_types.join(', ')}</span>
              </div>
            </div>
          ) : (
            <p className="text-slate-400">Configuration unavailable</p>
          )}
        </CardContent>
      </Card>

      {/* Email Configuration */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5" />
            Email Configuration
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-40" />
          ) : config ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Provider</span>
                <span className="font-medium capitalize">{config.email.provider}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">From Email</span>
                <span className="font-medium">{config.email.from_email}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">From Name</span>
                <span className="font-medium">{config.email.from_name}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">SMTP Host</span>
                <span className="font-medium">{config.email.smtp_host}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">SMTP Port</span>
                <span className="font-medium">{config.email.smtp_port}</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-slate-400">Use TLS</span>
                <Badge className={config.email.use_tls ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}>
                  {config.email.use_tls ? 'Enabled' : 'Disabled'}
                </Badge>
              </div>
            </div>
          ) : (
            <p className="text-slate-400">Configuration unavailable</p>
          )}
        </CardContent>
      </Card>

      {/* Storage Configuration */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Storage Configuration
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-40" />
          ) : config ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Provider</span>
                <span className="font-medium capitalize">{config.storage.provider}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Bucket Name</span>
                <span className="font-medium">{config.storage.bucket_name || 'Not configured'}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Region</span>
                <span className="font-medium">{config.storage.region || 'Not configured'}</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-slate-400">CDN URL</span>
                <span className="font-medium">{config.storage.cdn_url || 'Not configured'}</span>
              </div>
            </div>
          ) : (
            <p className="text-slate-400">Configuration unavailable</p>
          )}
        </CardContent>
      </Card>

      {/* Search Configuration */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Search Configuration
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-40" />
          ) : config ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Provider</span>
                <span className="font-medium capitalize">{config.search.provider}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Index Name</span>
                <span className="font-medium">{config.search.index_name}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Min Score</span>
                <span className="font-medium">{config.search.min_score}</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-slate-400">Fuzziness</span>
                <span className="font-medium">{config.search.fuzziness}</span>
              </div>
            </div>
          ) : (
            <p className="text-slate-400">Configuration unavailable</p>
          )}
        </CardContent>
      </Card>

      {/* Recommendation Configuration */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Recommendation Configuration
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-40" />
          ) : config ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Enabled</span>
                <Badge className={config.recommendation.enabled ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}>
                  {config.recommendation.enabled ? 'Enabled' : 'Disabled'}
                </Badge>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Strategy</span>
                <span className="font-medium capitalize">{config.recommendation.strategy.replace('_', ' ')}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Min Match Score</span>
                <span className="font-medium">{config.recommendation.min_match_score}</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-slate-400">Max Results</span>
                <span className="font-medium">{config.recommendation.max_results}</span>
              </div>
            </div>
          ) : (
            <p className="text-slate-400">Configuration unavailable</p>
          )}
        </CardContent>
      </Card>

      {/* Analytics Configuration */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Analytics Configuration
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-40" />
          ) : config ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Enabled</span>
                <Badge className={config.analytics.enabled ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}>
                  {config.analytics.enabled ? 'Enabled' : 'Disabled'}
                </Badge>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Provider</span>
                <span className="font-medium capitalize">{config.analytics.provider}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Tracking ID</span>
                <span className="font-medium">{config.analytics.tracking_id || 'Not configured'}</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-slate-400">Sample Rate</span>
                <span className="font-medium">{(config.analytics.sample_rate * 100).toFixed(0)}%</span>
              </div>
            </div>
          ) : (
            <p className="text-slate-400">Configuration unavailable</p>
          )}
        </CardContent>
      </Card>

      {/* Maintenance Mode */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            Maintenance Mode
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-40" />
          ) : config ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Maintenance Mode</span>
                <Badge className={config.maintenance.maintenance_mode ? 'bg-amber-500/10 text-amber-400' : 'bg-emerald-500/10 text-emerald-400'}>
                  {config.maintenance.maintenance_mode ? 'Active' : 'Inactive'}
                </Badge>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Maintenance Message</span>
                <span className="font-medium">{config.maintenance.maintenance_message || 'Not configured'}</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-slate-400">Scheduled Maintenance</span>
                <span className="font-medium">{config.maintenance.scheduled_maintenance ? new Date(config.maintenance.scheduled_maintenance).toLocaleString() : 'Not scheduled'}</span>
              </div>
            </div>
          ) : (
            <p className="text-slate-400">Configuration unavailable</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
