import React from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Search, 
  Filter, 
  Eye, 
  Clock, 
  CheckCircle2,
  XCircle,
  AlertTriangle
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { SearchAnalytics as SearchAnalyticsType } from '../types';
import { cn } from '@/lib/utils';

interface SearchAnalyticsProps {
  analytics: SearchAnalyticsType;
  className?: string;
}

export const SearchAnalytics: React.FC<SearchAnalyticsProps> = ({
  analytics,
  className,
}) => {
  const formatNumber = (num: number) => {
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}k`;
    }
    return num.toString();
  };

  const formatPercentage = (num: number) => {
    return `${(num * 100).toFixed(1)}%`;
  };

  const formatTime = (ms: number) => {
    if (ms < 1000) {
      return `${ms}ms`;
    }
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <div className={cn('space-y-6', className)}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-blue-500" />
            Search Analytics
          </h2>
          <p className="text-muted-foreground mt-1">
            Insights into search performance and user behavior
          </p>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Searches"
          value={formatNumber(analytics.total_searches)}
          icon={Search}
          trend="+12.5%"
          trendUp
        />
        <MetricCard
          title="Avg Results/Search"
          value={analytics.average_results_per_search.toFixed(1)}
          icon={BarChart3}
          trend="+5.2%"
          trendUp
        />
        <MetricCard
          title="Recommendation Rate"
          value={formatPercentage(analytics.recommendation_acceptance_rate)}
          icon={TrendingUp}
          trend="+8.1%"
          trendUp
        />
        <MetricCard
          title="Avg Response Time"
          value={formatTime(analytics.average_response_time)}
          icon={Clock}
          trend="-15%"
          trendUp={false}
        />
      </div>

      <Tabs defaultValue="popular" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="popular">Popular Searches</TabsTrigger>
          <TabsTrigger value="filters">Filter Usage</TabsTrigger>
          <TabsTrigger value="zero">Zero Results</TabsTrigger>
          <TabsTrigger value="views">Most Viewed</TabsTrigger>
        </TabsList>

        {/* Popular Searches */}
        <TabsContent value="popular" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Most Popular Search Queries</CardTitle>
            </CardHeader>
            <CardContent>
              {analytics.popular_queries.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No search data available yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {analytics.popular_queries.map((item, index) => (
                    <div key={item.query} className="flex items-center justify-between p-3 rounded-lg hover:bg-muted transition-colors">
                      <div className="flex items-center gap-3">
                        <Badge variant="outline" className="w-8 h-8 flex items-center justify-center rounded-full">
                          {index + 1}
                        </Badge>
                        <span className="font-medium">{item.query}</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <div className="text-sm font-semibold">{formatNumber(item.count)}</div>
                          <div className="text-xs text-muted-foreground">searches</div>
                        </div>
                        <div className="w-24">
                          <Progress 
                            value={(item.count / analytics.popular_queries[0].count) * 100} 
                            className="h-2"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Filter Usage */}
        <TabsContent value="filters" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Filter Usage Statistics</CardTitle>
            </CardHeader>
            <CardContent>
              {Object.keys(analytics.filter_usage).length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Filter className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No filter usage data available yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {Object.entries(analytics.filter_usage)
                    .sort(([, a], [, b]) => b - a)
                    .map(([filter, count]) => (
                      <div key={filter} className="flex items-center justify-between p-3 rounded-lg hover:bg-muted transition-colors">
                        <div className="flex items-center gap-3">
                          <Filter className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium capitalize">{filter.replace('_', ' ')}</span>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <div className="text-sm font-semibold">{formatNumber(count)}</div>
                            <div className="text-xs text-muted-foreground">uses</div>
                          </div>
                          <div className="w-24">
                            <Progress 
                              value={(count / Math.max(...Object.values(analytics.filter_usage))) * 100} 
                              className="h-2"
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Zero Result Queries */}
        <TabsContent value="zero" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-orange-500" />
                Queries with Zero Results
              </CardTitle>
            </CardHeader>
            <CardContent>
              {analytics.zero_result_queries.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <CheckCircle2 className="h-12 w-12 mx-auto mb-4 text-green-500" />
                  <p className="text-green-600 font-medium">All searches are returning results!</p>
                  <p className="text-sm mt-1">Great job on content coverage</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {analytics.zero_result_queries.map((query, index) => (
                    <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-orange-50 border border-orange-200">
                      <div className="flex items-center gap-3">
                        <XCircle className="h-4 w-4 text-orange-500" />
                        <span className="font-medium">{query}</span>
                      </div>
                      <Badge variant="outline" className="text-orange-800 border-orange-300">
                        No results
                      </Badge>
                    </div>
                  ))}
                  <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <p className="text-sm text-blue-800">
                      <strong>Recommendation:</strong> Consider adding more content or improving search indexing for these queries.
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Most Viewed Results */}
        <TabsContent value="views" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Eye className="h-5 w-5 text-blue-500" />
                Most Viewed Results
              </CardTitle>
            </CardHeader>
            <CardContent>
              {analytics.most_viewed_results.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Eye className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No view data available yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {analytics.most_viewed_results.map((item, index) => (
                    <div key={`${item.id}-${item.type}`} className="flex items-center justify-between p-3 rounded-lg hover:bg-muted transition-colors">
                      <div className="flex items-center gap-3">
                        <Badge variant="outline" className="w-8 h-8 flex items-center justify-center rounded-full">
                          {index + 1}
                        </Badge>
                        <div>
                          <div className="font-medium">{item.type}</div>
                          <div className="text-xs text-muted-foreground">ID: {item.id}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <div className="text-sm font-semibold">{formatNumber(item.views)}</div>
                          <div className="text-xs text-muted-foreground">views</div>
                        </div>
                        <div className="w-24">
                          <Progress 
                            value={(item.views / analytics.most_viewed_results[0].views) * 100} 
                            className="h-2"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Performance Insights */}
      <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-blue-500" />
            Performance Insights
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3 p-3 bg-white/50 rounded-lg">
            <CheckCircle2 className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
            <div>
              <div className="font-medium">Search Success Rate</div>
              <div className="text-sm text-muted-foreground">
                {analytics.zero_result_queries.length === 0 
                  ? 'Excellent - All searches return results'
                  : `${((1 - analytics.zero_result_queries.length / analytics.total_searches) * 100).toFixed(1)}% of searches return results`}
              </div>
            </div>
          </div>

          <div className="flex items-start gap-3 p-3 bg-white/50 rounded-lg">
            <Clock className="h-5 w-5 text-blue-500 mt-0.5 flex-shrink-0" />
            <div>
              <div className="font-medium">Response Time</div>
              <div className="text-sm text-muted-foreground">
                {analytics.average_response_time < 500 
                  ? 'Excellent - Fast search performance'
                  : analytics.average_response_time < 1000
                  ? 'Good - Acceptable search performance'
                  : 'Needs improvement - Consider optimization'}
              </div>
            </div>
          </div>

          <div className="flex items-start gap-3 p-3 bg-white/50 rounded-lg">
            <TrendingUp className="h-5 w-5 text-purple-500 mt-0.5 flex-shrink-0" />
            <div>
              <div className="font-medium">Recommendation Acceptance</div>
              <div className="text-sm text-muted-foreground">
                {analytics.recommendation_acceptance_rate > 0.7 
                  ? 'Excellent - Users find recommendations helpful'
                  : analytics.recommendation_acceptance_rate > 0.5
                  ? 'Good - Moderate recommendation acceptance'
                  : 'Needs improvement - Review recommendation algorithm'}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

interface MetricCardProps {
  title: string;
  value: string;
  icon: React.ElementType;
  trend: string;
  trendUp: boolean;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, icon: Icon, trend, trendUp }) => {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-2">
          <Icon className="h-5 w-5 text-muted-foreground" />
          <Badge 
            variant={trendUp ? 'default' : 'secondary'}
            className={cn(trendUp ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800')}
          >
            {trend}
          </Badge>
        </div>
        <div className="text-2xl font-bold">{value}</div>
        <div className="text-sm text-muted-foreground mt-1">{title}</div>
      </CardContent>
    </Card>
  );
};
