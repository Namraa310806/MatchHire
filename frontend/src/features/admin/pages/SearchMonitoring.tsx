import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useSearchMetrics } from '../hooks/useObservability';
import { Search, Database, Activity, TrendingUp, AlertTriangle } from 'lucide-react';

export default function SearchMonitoring() {
  const { data: metrics, isLoading } = useSearchMetrics();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Search Platform Monitoring</h1>
        <p className="text-slate-400 mt-2">Search provider performance and metrics</p>
      </div>

      {/* Provider Info */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Search Provider
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-20" />
          ) : metrics ? (
            <div className="grid gap-4 md:grid-cols-3">
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Provider</p>
                <p className="text-2xl font-bold capitalize">{metrics.provider}</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Index Status</p>
                <p className="text-2xl font-bold capitalize">{metrics.index_status}</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Document Count</p>
                <p className="text-2xl font-bold">{metrics.document_count.toLocaleString()}</p>
              </div>
            </div>
          ) : (
            <p className="text-slate-400">Metrics unavailable</p>
          )}
        </CardContent>
      </Card>

      {/* Performance Metrics */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Performance Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="grid gap-4 md:grid-cols-2">
              {[...Array(4)].map((_, i) => (
                <Skeleton key={i} className="h-20" />
              ))}
            </div>
          ) : metrics ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Query Latency (p50)</p>
                <p className="text-2xl font-bold">{metrics.query_latency_p50.toFixed(0)}ms</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Query Latency (p95)</p>
                <p className="text-2xl font-bold">{metrics.query_latency_p95.toFixed(0)}ms</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Query Latency (p99)</p>
                <p className="text-2xl font-bold">{metrics.query_latency_p99.toFixed(0)}ms</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Index Latency (p50)</p>
                <p className="text-2xl font-bold">{metrics.index_latency_p50.toFixed(0)}ms</p>
              </div>
            </div>
          ) : (
            <p className="text-slate-400">Metrics unavailable</p>
          )}
        </CardContent>
      </Card>

      {/* Usage Metrics */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Usage Metrics
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
                <p className="text-sm text-slate-400">Total Queries</p>
                <p className="text-2xl font-bold">{metrics.total_queries.toLocaleString()}</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Cache Hit Ratio</p>
                <p className="text-2xl font-bold">{(metrics.cache_hit_ratio * 100).toFixed(1)}%</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Search Failures</p>
                <p className="text-2xl font-bold text-red-400">{metrics.search_failures.toLocaleString()}</p>
              </div>
            </div>
          ) : (
            <p className="text-slate-400">Metrics unavailable</p>
          )}
        </CardContent>
      </Card>

      {/* Top Queries */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Top Queries
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12" />
              ))}
            </div>
          ) : metrics && metrics.top_queries.length > 0 ? (
            <div className="space-y-3">
              {metrics.top_queries.map((query, index) => (
                <div key={index} className="flex items-center justify-between p-3 rounded-lg border border-slate-800 bg-slate-800/50">
                  <p className="font-medium">{query.query}</p>
                  <div className="flex items-center gap-4 text-sm text-slate-400">
                    <span>{query.count} searches</span>
                    <span>{query.avg_latency_ms.toFixed(0)}ms avg</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <AlertTriangle className="h-12 w-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">No query data available</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
