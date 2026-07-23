import api from '@/lib/api';

export interface Notification {
  id: string;
  recipient: string;
  type: 'application' | 'interview' | 'recommendation' | 'candidate_activity' | 'system';
  title: string;
  message: string;
  data?: Record<string, any>;
  is_read: boolean;
  created_at: string;
}

export interface NotificationPreferences {
  email_notifications: boolean;
  push_notifications: boolean;
  application_alerts: boolean;
  interview_reminders: boolean;
  recommendation_alerts: boolean;
  candidate_activity_alerts: boolean;
}

export const notificationService = {
  // Get notifications
  getNotifications: async (unreadOnly: boolean = false): Promise<Notification[]> => {
    const params = unreadOnly ? { unread_only: true } : {};
    const response = await api.get('/notifications/', { params });
    return response.data;
  },

  // Get unread count
  getUnreadCount: async (): Promise<{ count: number }> => {
    const response = await api.get('/notifications/unread-count/');
    return response.data;
  },

  // Mark as read
  markAsRead: async (id: string): Promise<void> => {
    await api.patch(`/notifications/${id}/read/`);
  },

  // Mark all as read
  markAllAsRead: async (): Promise<void> => {
    await api.post('/notifications/mark-all-read/');
  },

  // Delete notification
  deleteNotification: async (id: string): Promise<void> => {
    await api.delete(`/notifications/${id}/`);
  },

  // Get notification preferences
  getPreferences: async (): Promise<NotificationPreferences> => {
    const response = await api.get('/notifications/preferences/');
    return response.data;
  },

  // Update notification preferences
  updatePreferences: async (
    data: Partial<NotificationPreferences>
  ): Promise<NotificationPreferences> => {
    const response = await api.patch('/notifications/preferences/', data);
    return response.data;
  },
};
