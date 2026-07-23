import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { useSystemMetrics } from '../hooks/useObservability';
import { Activity, Zap, AlertTriangle, Clock, Server, Cpu, Network } from 'lucide-react';

export default function Observability() {
  const { data: metrics, isLoading } = useSystemMetrics();

  const getServiceStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-emerald-400 bg-emerald-400/10';
      case 'degraded':
        return 'text-amber-400 bg-amber-400/10';
      case 'unhealthy':
        return 'text-red-400 bg-red-400/10';
      default:
        return 'text-slate-400 bg-slate-400/10';
    }
  };

  const getJobStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'text-emerald-400 bg-emerald-400/10';
      case 'idle':
        return 'text-slate-400 bg-slate-400/10';
      case 'failed':
        return 'text-red-400 bg-red-400/10';
      default:
        return 'text-slate-400 bg-slate-400/10';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Observability</h1>
        <p className="text-slate-400 mt-2">System performance, health, and operational metrics</p>
      </div>

      {/* API Performance */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            API Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="grid gap-4 md:grid-cols-3">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-20" />
              ))}
            </div>
          ) : metrics ? (
            <div className="grid gap-4 md:grid-cols-3">
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">API Latency (p50)</p>
                <p className="text-2xl font-bold">{metrics.api_latency_p50.toFixed(0)}ms</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">API Latency (p95)</p>
                <p className="text-2xl font-bold">{metrics.api_latency_p95.toFixed(0)}ms</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">API Latency (p99)</p>
                <p className="text-2xl font-bold">{metrics.api_latency_p99.toFixed(0)}ms</p>
              </div>
            </div>
          ) : (
            <p className="text-slate-400">Metrics unavailable</p>
          )}
        </CardContent>
      </Card>

      {/* Request Volume & Error Rate */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5" />
              Request Volume
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-20" />
            ) : metrics ? (
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Total Requests</p>
                <p className="text-3xl font-bold">{metrics.request_volume.toLocaleString()}</p>
                <p className="text-sm text-slate-400 mt-2">Current period</p>
              </div>
            ) : (
              <p className="text-slate-400">Metrics unavailable</p>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              Error Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-20" />
            ) : metrics ? (
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Error Rate</p>
                <p className="text-3xl font-bold">{(metrics.error_rate * 100).toFixed(2)}%</p>
                <p className="text-sm text-slate-400 mt-2">Current period</p>
              </div>
            ) : (
              <p className="text-slate-400">Metrics unavailable</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Cache Performance */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />
            Cache Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-20" />
          ) : metrics ? (
            <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
              <p className="text-sm text-slate-400">Cache Hit Ratio</p>
              <p className="text-3xl font-bold">{(metrics.cache_hit_ratio * 100).toFixed(1)}%</p>
              <div className="mt-4 h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 transition-all"
                  style={{ width: `${metrics.cache_hit_ratio * 100}%` }}
                />
              </div>
            </div>
          ) : (
            <p className="text-slate-400">Metrics unavailable</p>
          )}
        </CardContent>
      </Card>

      {/* Queue Status */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Queue Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-16" />
              ))}
            </div>
          ) : metrics && metrics.queue_status.length > 0 ? (
            <div className="space-y-3">
              {metrics.queue_status.map((queue) => (
                <div key={queue.name} className="flex items-center justify-between p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                  <div>
                    <p className="font-medium">{queue.name}</p>
                    <p className="text-sm text-slate-400">
                      {queue.processing} processing · {queue.failed} failed
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold">{queue.size}</p>
                    <p className="text-sm text-slate-400">queued</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Clock className="h-12 w-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">No queue data available</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Background Jobs */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="h-5 w-5" />
            Background Jobs
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-16" />
              ))}
            </div>
          ) : metrics && metrics.background_jobs.length > 0 ? (
            <div className="space-y-3">
              {metrics.background_jobs.map((job) => (
                <div key={job.name} className="flex items-center justify-between p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                  <div className="flex items-center gap-3">
                    <Badge className={getJobStatusColor(job.status)} variant="outline">
                      {job.status}
                    </Badge>
                    <div>
                      <p className="font-medium">{job.name}</p>
                      <p className="text-sm text-slate-400">
                        Last run: {job.last_run ? new Date(job.last_run).toLocaleString() : 'Never'}
                      </p>
                    </div>
                  </div>
                  {job.next_run && (
                    <p className="text-sm text-slate-400">
                      Next: {new Date(job.next_run).toLocaleString()}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Cpu className="h-12 w-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">No background job data available</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Service Health */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="h-5 w-5" />
            Service Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-16" />
              ))}
            </div>
          ) : metrics && metrics.service_health.length > 0 ? (
            <div className="space-y-3">
              {metrics.service_health.map((service) => (
                <div key={service.name} className="flex items-center justify-between p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                  <div className="flex items-center gap-3">
                    <Badge className={getServiceStatusColor(service.status)} variant="outline">
                      {service.status}
                    </Badge>
                    <div>
                      <p className="font-medium">{service.name}</p>
                      <p className="text-sm text-slate-400">
                        Last check: {new Date(service.last_check).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold">{(service.uptime / 3600).toFixed(1)}h</p>
                    <p className="text-sm text-slate-400">uptime</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Network className="h-12 w-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">No service health data available</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
