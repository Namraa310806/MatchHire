import api from '@/lib/api';

export interface Notification {
  id: string;
  recipient: string;
  notification_type: string;
  title: string;
  message: string;
  data?: any;
  is_read: boolean;
  created_at: string;
  priority?: 'low' | 'medium' | 'high';
}

export const notificationService = {
  // Get all notifications
  getNotifications: async (): Promise<Notification[]> => {
    const response = await api.get('/notifications/');
    return response.data;
  },

  // Mark notification as read
  markAsRead: async (id: string): Promise<void> => {
    await api.post(`/notifications/${id}/read/`);
  },

  // Mark all notifications as read
  markAllAsRead: async (): Promise<void> => {
    await api.post('/notifications/read-all/');
  },

  // Get unread count
  getUnreadCount: async (): Promise<number> => {
    const response = await api.get('/notifications/unread-count/');
    return response.data.count;
  },
};
