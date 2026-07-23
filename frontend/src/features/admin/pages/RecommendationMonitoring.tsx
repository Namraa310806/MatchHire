import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useRecommendationMetrics } from '../hooks/useObservability';
import { Brain, Activity, TrendingUp, ThumbsUp, ThumbsDown } from 'lucide-react';

export default function RecommendationMonitoring() {
  const { data: metrics, isLoading } = useRecommendationMetrics();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Recommendation Engine Monitoring</h1>
        <p className="text-slate-400 mt-2">Recommendation performance and feedback metrics</p>
      </div>

      {/* Overview Metrics */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Overview
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
                <p className="text-sm text-slate-400">Total Requests</p>
                <p className="text-2xl font-bold">{metrics.total_requests.toLocaleString()}</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Acceptance Rate</p>
                <p className="text-2xl font-bold">{(metrics.acceptance_rate * 100).toFixed(1)}%</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Avg Confidence</p>
                <p className="text-2xl font-bold">{(metrics.avg_confidence * 100).toFixed(1)}%</p>
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
            Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="grid gap-4 md:grid-cols-2">
              {[...Array(2)].map((_, i) => (
                <Skeleton key={i} className="h-20" />
              ))}
            </div>
          ) : metrics ? (
            <div className="grid gap-4 md:grid-cols-2">
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Latency (p50)</p>
                <p className="text-2xl font-bold">{metrics.latency_p50.toFixed(0)}ms</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400">Latency (p95)</p>
                <p className="text-2xl font-bold">{metrics.latency_p95.toFixed(0)}ms</p>
              </div>
            </div>
          ) : (
            <p className="text-slate-400">Metrics unavailable</p>
          )}
        </CardContent>
      </Card>

      {/* Feedback Metrics */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Feedback
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
                <p className="text-sm text-slate-400">Total Feedback</p>
                <p className="text-2xl font-bold">{metrics.feedback_count.toLocaleString()}</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400 flex items-center gap-2">
                  <ThumbsUp className="h-4 w-4 text-emerald-400" />
                  Positive
                </p>
                <p className="text-2xl font-bold text-emerald-400">{metrics.positive_feedback.toLocaleString()}</p>
              </div>
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-800/50">
                <p className="text-sm text-slate-400 flex items-center gap-2">
                  <ThumbsDown className="h-4 w-4 text-red-400" />
                  Negative
                </p>
                <p className="text-2xl font-bold text-red-400">{metrics.negative_feedback.toLocaleString()}</p>
              </div>
            </div>
          ) : (
            <p className="text-slate-400">Metrics unavailable</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
