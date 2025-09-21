import api from './api';

export const getNotifications = async () => {
  return api.get('/notifications');
};

export const markAsRead = async (id: string) => {
  return api.put(`/notifications/${id}/read`);
};

export const markAllAsRead = async () => {
  return api.put('/notifications/read-all');
};

export const deleteNotification = async (id: string) => {
  return api.delete(`/notifications/${id}`);
};