import api from '@/lib/api'

export interface Notification {
  id: string
  userId: string
  type: 'application' | 'interview' | 'offer' | 'message' | 'system'
  title: string
  message: string
  data?: any
  read: boolean
  createdAt: string
}

export const notificationService = {
  getNotifications: async (userId: string, unreadOnly = false): Promise<Notification[]> => {
    const response = await api.get(`/notifications/${userId}`, {
      params: { unreadOnly }
    })
    return response.data
  },

  markAsRead: async (notificationId: string): Promise<void> => {
    await api.patch(`/notifications/${notificationId}/read`)
  },

  markAllAsRead: async (userId: string): Promise<void> => {
    await api.patch(`/notifications/${userId}/read-all`)
  },

  deleteNotification: async (notificationId: string): Promise<void> => {
    await api.delete(`/notifications/${notificationId}`)
  },

  getUnreadCount: async (userId: string): Promise<number> => {
    const response = await api.get(`/notifications/${userId}/unread-count`)
    return response.data.count
  },
}
