import { useState } from 'react';
import { useNotifications, useMarkAsRead, useMarkAllAsRead, useUnreadCount } from '@/features/notifications/hooks/useNotifications';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Spinner } from '@/components/ui/spinner';
import { EmptyState } from '@/components/ui/empty-state';
import { Bell, Check, CheckCircle, Briefcase, Calendar, FileText, X } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export default function NotificationsPage() {
  const { data: notifications, isLoading } = useNotifications();
  const { data: unreadCount } = useUnreadCount();
  const markAsRead = useMarkAsRead();
  const markAllAsRead = useMarkAllAsRead();
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  const handleMarkAsRead = (id: string) => {
    markAsRead.mutate(id);
  };

  const handleMarkAllAsRead = () => {
    markAllAsRead.mutate();
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'application':
        return <Briefcase className="h-5 w-5 text-blue-500" />;
      case 'interview':
        return <Calendar className="h-5 w-5 text-purple-500" />;
      case 'profile_view':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'job_alert':
        return <FileText className="h-5 w-5 text-orange-500" />;
      default:
        return <Bell className="h-5 w-5 text-gray-500" />;
    }
  };

  const filteredNotifications = notifications?.filter((notif: any) => {
    if (filter === 'unread') return !notif.read;
    return true;
  }) || [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Notifications</h1>
          <p className="text-muted-foreground mt-2">
            {unreadCount && unreadCount > 0
              ? `${unreadCount} unread notification${unreadCount > 1 ? 's' : ''}`
              : 'All caught up!'}
          </p>
        </div>
        {unreadCount && unreadCount > 0 && (
          <Button variant="outline" onClick={handleMarkAllAsRead} disabled={markAllAsRead.isPending}>
            <Check className="h-4 w-4 mr-2" />
            Mark All Read
          </Button>
        )}
      </div>

      <div className="flex gap-2">
        <Button
          variant={filter === 'all' ? 'default' : 'outline'}
          onClick={() => setFilter('all')}
        >
          All
        </Button>
        <Button
          variant={filter === 'unread' ? 'default' : 'outline'}
          onClick={() => setFilter('unread')}
        >
          Unread
        </Button>
      </div>

      {filteredNotifications.length > 0 ? (
        <div className="space-y-4">
          {filteredNotifications.map((notification) => (
            <NotificationCard
              key={notification.id}
              notification={notification}
              onMarkAsRead={() => handleMarkAsRead(notification.id)}
              getNotificationIcon={getNotificationIcon}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          title="No notifications"
          description={filter === 'unread' ? 'No unread notifications' : 'No notifications to display'}
        />
      )}
    </div>
  );
}

interface NotificationCardProps {
  notification: any;
  onMarkAsRead: () => void;
  getNotificationIcon: (type: string) => React.ReactNode;
}

function NotificationCard({ notification, onMarkAsRead, getNotificationIcon }: NotificationCardProps) {
  return (
    <Card className={!notification.read ? 'border-primary' : ''}>
      <CardContent className="pt-6">
        <div className="flex items-start gap-4">
          <div className={`p-3 rounded-lg ${!notification.read ? 'bg-primary/10' : 'bg-muted'}`}>
            {getNotificationIcon(notification.type)}
          </div>
          <div className="flex-1">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="font-medium">{notification.title}</p>
                <p className="text-sm text-muted-foreground mt-1">{notification.message}</p>
                <p className="text-xs text-muted-foreground mt-2">
                  {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
                </p>
              </div>
              {!notification.read && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onMarkAsRead}
                  className="ml-2"
                >
                  <Check className="h-4 w-4" />
                </Button>
              )}
            </div>
            {notification.action_url && (
              <Button variant="link" className="p-0 h-auto mt-2" asChild>
                <a href={notification.action_url}>View Details</a>
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
