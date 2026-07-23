import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useRecentActivity } from '../hooks';
import { formatDistanceToNow } from 'date-fns';
import { Briefcase, Users, FileText, Calendar, CheckCircle } from 'lucide-react';

export function ActivityTimeline() {
  const { data: activities, isLoading } = useRecentActivity();

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'job':
        return Briefcase;
      case 'candidate':
        return Users;
      case 'application':
        return FileText;
      case 'interview':
        return Calendar;
      default:
        return CheckCircle;
    }
  };

  const getActivityColor = (type: string) => {
    switch (type) {
      case 'job':
        return 'text-blue-500 bg-blue-500/10';
      case 'candidate':
        return 'text-green-500 bg-green-500/10';
      case 'application':
        return 'text-purple-500 bg-purple-500/10';
      case 'interview':
        return 'text-orange-500 bg-orange-500/10';
      default:
        return 'text-gray-500 bg-gray-500/10';
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex gap-3">
                <Skeleton className="h-8 w-8 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-48" />
                  <Skeleton className="h-3 w-32" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!activities || activities.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            No recent activity
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {activities.slice(0, 10).map((activity) => {
            const Icon = getActivityIcon(activity.type);
            return (
              <div key={activity.id} className="flex gap-3">
                <div
                  className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 ${getActivityColor(
                    activity.type
                  )}`}
                >
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{activity.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {activity.description}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {formatDistanceToNow(new Date(activity.timestamp), {
                      addSuffix: true,
                    })}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
