import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useNotifications, useMarkAsRead, useMarkAllAsRead } from '../hooks';
import { formatDistanceToNow } from 'date-fns';
import { Bell, Check, CheckCheck, X, Briefcase, Users, FileText, Calendar, MessageSquare } from 'lucide-react';
import React from 'react';

const NOTIFICATION_ICONS = {
  application: { icon: FileText, color: 'text-blue-500', bg: 'bg-blue-500/10' },
  interview: { icon: Calendar, color: 'text-purple-500', bg: 'bg-purple-500/10' },
  message: { icon: MessageSquare, color: 'text-green-500', bg: 'bg-green-500/10' },
  job: { icon: Briefcase, color: 'text-orange-500', bg: 'bg-orange-500/10' },
  candidate: { icon: Users, color: 'text-pink-500', bg: 'bg-pink-500/10' },
};

export function NotificationsPanel() {
  const { data: notifications, isLoading } = useNotifications();
  const markAsRead = useMarkAsRead();
  const markAllAsRead = useMarkAllAsRead();

  const handleMarkAsRead = async (id: string) => {
    try {
      await markAsRead.mutateAsync(id);
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await markAllAsRead.mutateAsync();
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  };

  const unreadCount = notifications?.filter((n) => !n.read).length || 0;

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <Card key={i}>
            <CardContent className="p-4">
              <Skeleton className="h-12 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-2xl font-bold">Notifications</h2>
          {unreadCount > 0 && (
            <Badge variant="default">{unreadCount} unread</Badge>
          )}
        </div>
        {unreadCount > 0 && (
          <Button variant="outline" size="sm" onClick={handleMarkAllAsRead}>
            <CheckCheck className="h-4 w-4 mr-2" />
            Mark all as read
          </Button>
        )}
      </div>

      {/* Notifications List */}
      {!notifications || notifications.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Bell className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No notifications</h3>
            <p className="text-muted-foreground">
              You're all caught up! We'll notify you when something important happens.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {notifications.map((notification) => {
            const iconInfo = NOTIFICATION_ICONS[notification.type as keyof typeof NOTIFICATION_ICONS] || NOTIFICATION_ICONS.application;
            const Icon = iconInfo.icon;

            return (
              <Card
                key={notification.id}
                className={`transition-colors ${!notification.read ? 'bg-muted/50 border-primary' : ''}`}
              >
                <CardContent className="p-4">
                  <div className="flex gap-4">
                    <div className={`p-3 rounded-lg ${iconInfo.bg}`}>
                      <Icon className={`h-5 w-5 ${iconInfo.color}`} />
                    </div>

                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-1">
                        <div className="flex-1">
                          <p className="font-medium">{notification.title}</p>
                          <p className="text-sm text-muted-foreground">{notification.message}</p>
                        </div>
                        {!notification.read && (
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => handleMarkAsRead(notification.id)}
                          >
                            <Check className="h-4 w-4" />
                          </Button>
                        )}
                      </div>

                      <div className="flex items-center justify-between mt-2">
                        <p className="text-xs text-muted-foreground">
                          {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
                        </p>
                        {notification.action_url && (
                          <Button variant="link" size="sm" className="h-auto p-0">
                            View
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
