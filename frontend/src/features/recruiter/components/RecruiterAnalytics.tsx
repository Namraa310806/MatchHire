import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import {
  useHiringFunnel,
  useTimeToHire,
  useApplicationTrends,
  useJobPerformance,
  useRecruiterActivity,
} from '../hooks';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444'];

export function RecruiterAnalytics() {
  const [timeRange, setTimeRange] = React.useState('30d');
  const { data: hiringFunnel, isLoading: isLoadingFunnel } = useHiringFunnel(timeRange);
  const { data: timeToHire, isLoading: isLoadingTimeToHire } = useTimeToHire(timeRange);
  const { data: applicationTrends, isLoading: isLoadingTrends } = useApplicationTrends(timeRange);
  const { data: jobPerformance, isLoading: isLoadingJobs } = useJobPerformance(timeRange);
  const { data: recruiterActivity, isLoading: isLoadingActivity } = useRecruiterActivity(timeRange);

  if (isLoadingFunnel || isLoadingTimeToHire || isLoadingTrends || isLoadingJobs || isLoadingActivity) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Recruiter Analytics</h2>
          <p className="text-muted-foreground">Track your hiring performance and metrics</p>
        </div>
        <Select value={timeRange} onValueChange={setTimeRange}>
          <SelectTrigger className="w-[180px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7d">Last 7 days</SelectItem>
            <SelectItem value="30d">Last 30 days</SelectItem>
            <SelectItem value="90d">Last 90 days</SelectItem>
            <SelectItem value="1y">Last year</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Hiring Funnel */}
      <Card>
        <CardHeader>
          <CardTitle>Hiring Funnel</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={hiringFunnel}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="stage" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#3b82f6" name="Candidates" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Time to Hire */}
      <Card>
        <CardHeader>
          <CardTitle>Average Time to Hire</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timeToHire}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="days" stroke="#8b5cf6" strokeWidth={2} name="Days" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Application Trends */}
      <Card>
        <CardHeader>
          <CardTitle>Application Trends</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={applicationTrends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="applications" stroke="#10b981" strokeWidth={2} name="Applications" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Job Performance */}
      <Card>
        <CardHeader>
          <CardTitle>Job Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={jobPerformance}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="job" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="applications" fill="#3b82f6" name="Applications" />
              <Bar dataKey="hired" fill="#10b981" name="Hired" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Recruiter Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recruiter Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={recruiterActivity}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => entry.name}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {recruiterActivity?.map((entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
