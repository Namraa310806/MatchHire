import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { StatCard } from '@/components/ui/stat-card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { useAdminDashboard } from '../hooks/useAdminDashboard';
import { useHealthStatus } from '../hooks/useHealth';
import { useSearchMetrics } from '../hooks/useObservability';
import { useRecommendationMetrics } from '../hooks/useObservability';
import { useSystemMetrics } from '../hooks/useObservability';
import { Activity, Users, Briefcase, FileText, Database, Search, Brain, AlertCircle, CheckCircle, Clock, TrendingUp } from 'lucide-react';

export default function SystemDashboard() {
  const { data: dashboardStats, isLoading: statsLoading } = useAdminDashboard();
  const { data: healthStatus, isLoading: healthLoading } = useHealthStatus();
  const { data: searchMetrics, isLoading: searchLoading } = useSearchMetrics();
  const { data: recommendationMetrics, isLoading: recommendationLoading } = useRecommendationMetrics();
  const { data: systemMetrics, isLoading: systemLoading } = useSystemMetrics();

  const getHealthStatusColor = (status: string) => {
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

  const getHealthStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4" />;
      case 'degraded':
        return <AlertCircle className="h-4 w-4" />;
      case 'unhealthy':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">System Dashboard</h1>
          <p className="text-slate-400 mt-2">Platform health, metrics, and real-time monitoring</p>
        </div>
        {healthStatus && (
          <Badge className={getHealthStatusColor(healthStatus.status)}>
            {getHealthStatusIcon(healthStatus.status)}
            <span className="ml-2 capitalize">{healthStatus.status}</span>
          </Badge>
        )}
      </div>

      {/* Platform KPIs */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Users"
          value={statsLoading ? 0 : dashboardStats?.total_users || 0}
          description="Registered users"
          icon={Users}
          trend={statsLoading ? undefined : { value: 12, isPositive: true }}
          loading={statsLoading}
        />
        <StatCard
          title="Active Jobs"
          value={statsLoading ? 0 : dashboardStats?.active_jobs || 0}
          description="Active job listings"
          icon={Briefcase}
          trend={statsLoading ? undefined : { value: 8, isPositive: true }}
          loading={statsLoading}
        />
        <StatCard
          title="Applications"
          value={statsLoading ? 0 : dashboardStats?.total_applications || 0}
          description="Total applications"
          icon={FileText}
          trend={statsLoading ? undefined : { value: 15, isPositive: true }}
          loading={statsLoading}
        />
        <StatCard
          title="Companies"
          value={statsLoading ? 0 : dashboardStats?.total_companies || 0}
          description="Registered companies"
          icon={Activity}
          trend={statsLoading ? undefined : { value: 5, isPositive: true }}
          loading={statsLoading}
        />
      </div>

      {/* Secondary KPIs */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Active Users"
          value={statsLoading ? 0 : dashboardStats?.active_users || 0}
          description="Users active in last 30 days"
          icon={Users}
          loading={statsLoading}
        />
        <StatCard
          title="Pending Jobs"
          value={statsLoading ? 0 : dashboardStats?.pending_jobs || 0}
          description="Jobs awaiting approval"
          icon={Briefcase}
          loading={statsLoading}
        />
        <StatCard
          title="Interviews"
          value={statsLoading ? 0 : dashboardStats?.total_interviews || 0}
          description="Scheduled interviews"
          icon={Clock}
          loading={statsLoading}
        />
        <StatCard
          title="Matches"
          value={statsLoading ? 0 : dashboardStats?.total_matches || 0}
          description="Candidate-job matches"
          icon={TrendingUp}
          loading={statsLoading}
        />
      </div>

      {/* System Health */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            System Health
          </CardTitle>
          <CardDescription>Real-time health checks for all system components</CardDescription>
        </CardHeader>
        <CardContent>
          {healthLoading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex items-center justify-between">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-4 w-24" />
                </div>
              ))}
            </div>
          ) : healthStatus ? (
            <div className="space-y-3">
              {healthStatus.checks.map((check) => (
                <div key={check.name} className="flex items-center justify-between py-2 border-b border-slate-800 last:border-0">
                  <div className="flex items-center gap-3">
                    {getHealthStatusIcon(check.status)}
                    <span className="font-medium capitalize">{check.name}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-slate-400">{check.message}</span>
                    <Badge className={getHealthStatusColor(check.status)} variant="outline">
                      {check.duration_ms.toFixed(0)}ms
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-slate-400">Health status unavailable</p>
          )}
        </CardContent>
      </Card>

      {/* Search Platform Metrics */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Search Platform
          </CardTitle>
          <CardDescription>Search provider performance and metrics</CardDescription>
        </CardHeader>
        <CardContent>
          {searchLoading ? (
            <div className="grid gap-4 md:grid-cols-3">
              {[...Array(6)].map((_, i) => (
                <Skeleton key={i} className="h-20" />
              ))}
            </div>
          ) : searchMetrics ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Provider</p>
                <p className="text-2xl font-bold capitalize">{searchMetrics.provider}</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Index Status</p>
                <p className="text-2xl font-bold capitalize">{searchMetrics.index_status}</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Document Count</p>
                <p className="text-2xl font-bold">{searchMetrics.document_count.toLocaleString()}</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Query Latency (p50)</p>
                <p className="text-2xl font-bold">{searchMetrics.query_latency_p50.toFixed(0)}ms</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Query Latency (p95)</p>
                <p className="text-2xl font-bold">{searchMetrics.query_latency_p95.toFixed(0)}ms</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Cache Hit Ratio</p>
                <p className="text-2xl font-bold">{(searchMetrics.cache_hit_ratio * 100).toFixed(1)}%</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Total Queries</p>
                <p className="text-2xl font-bold">{searchMetrics.total_queries.toLocaleString()}</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Search Failures</p>
                <p className="text-2xl font-bold text-red-400">{searchMetrics.search_failures.toLocaleString()}</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Index Latency (p50)</p>
                <p className="text-2xl font-bold">{searchMetrics.index_latency_p50.toFixed(0)}ms</p>
              </div>
            </div>
          ) : (
            <p className="text-slate-400">Search metrics unavailable</p>
          )}
        </CardContent>
      </Card>

      {/* Recommendation Engine Metrics */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Recommendation Engine
          </CardTitle>
          <CardDescription>Recommendation performance and feedback metrics</CardDescription>
        </CardHeader>
        <CardContent>
          {recommendationLoading ? (
            <div className="grid gap-4 md:grid-cols-3">
              {[...Array(6)].map((_, i) => (
                <Skeleton key={i} className="h-20" />
              ))}
            </div>
          ) : recommendationMetrics ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Total Requests</p>
                <p className="text-2xl font-bold">{recommendationMetrics.total_requests.toLocaleString()}</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Acceptance Rate</p>
                <p className="text-2xl font-bold">{(recommendationMetrics.acceptance_rate * 100).toFixed(1)}%</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Avg Confidence</p>
                <p className="text-2xl font-bold">{(recommendationMetrics.avg_confidence * 100).toFixed(1)}%</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Latency (p50)</p>
                <p className="text-2xl font-bold">{recommendationMetrics.latency_p50.toFixed(0)}ms</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Latency (p95)</p>
                <p className="text-2xl font-bold">{recommendationMetrics.latency_p95.toFixed(0)}ms</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Feedback Count</p>
                <p className="text-2xl font-bold">{recommendationMetrics.feedback_count.toLocaleString()}</p>
              </div>
            </div>
          ) : (
            <p className="text-slate-400">Recommendation metrics unavailable</p>
          )}
        </CardContent>
      </Card>

      {/* System Metrics */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            System Metrics
          </CardTitle>
          <CardDescription>API performance, request volume, and system observability</CardDescription>
        </CardHeader>
        <CardContent>
          {systemLoading ? (
            <div className="grid gap-4 md:grid-cols-3">
              {[...Array(6)].map((_, i) => (
                <Skeleton key={i} className="h-20" />
              ))}
            </div>
          ) : systemMetrics ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">API Latency (p50)</p>
                <p className="text-2xl font-bold">{systemMetrics.api_latency_p50.toFixed(0)}ms</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">API Latency (p95)</p>
                <p className="text-2xl font-bold">{systemMetrics.api_latency_p95.toFixed(0)}ms</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">API Latency (p99)</p>
                <p className="text-2xl font-bold">{systemMetrics.api_latency_p99.toFixed(0)}ms</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Request Volume</p>
                <p className="text-2xl font-bold">{systemMetrics.request_volume.toLocaleString()}</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Error Rate</p>
                <p className="text-2xl font-bold">{(systemMetrics.error_rate * 100).toFixed(2)}%</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Cache Hit Ratio</p>
                <p className="text-2xl font-bold">{(systemMetrics.cache_hit_ratio * 100).toFixed(1)}%</p>
              </div>
            </div>
          ) : (
            <p className="text-slate-400">System metrics unavailable</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
